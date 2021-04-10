from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup
import requests
import textile
import sys
import os


class RadioJavanScraping:
    
    chrome_path = os.path.realpath('chromedriver')
    chrome_options = webdriver.ChromeOptions()
    chrome_options.accept_untrusted_certs = True
    chrome_options.assume_untrusted_cert_issuer = True
    capa = DesiredCapabilities.CHROME
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--start-maximized")
    browser = webdriver.Chrome(executable_path=chrome_path, chrome_options=chrome_options, desired_capabilities=capa)

    def download(self, num_retries=2):

        url = input("Enter URL: ")
        print("Downloading URL...")
        try:
            resp = requests.get(url)
            html = resp.text
            if resp.status_code >= 400:
                print('Download error:', resp.text)
                html = None
                if num_retries and 500 <= resp.status_code < 600:
                    # recursively retry 5xx HTTP errors
                    return self.download(num_retries - 1)
        except requests.exceptions.RequestException as e:
            html = None

        return html

    def check_box_id(self, name):
        data = {'log': '', 'pwd': '***'}
        session = requests.session()
        session.post('http://lyricsy.ir/wp-login.php', data=data)
        new_post_page = session.get('http://lyricsy.ir/wp-admin/post-new.php')
        soup = BeautifulSoup(new_post_page.content, 'html.parser')

        checkbox_dic = {}
        a, b = [], []
        for key in soup.find(id='categorychecklist').findAll('label'):
            a.append(key.text.lstrip())
        for value in soup.find(id='categorychecklist').findAll('input'):
            b.append(value['id'])
        for i in range(len(a)):
            checkbox_dic[a[i]] = b[i]
        print('Started...')
        return checkbox_dic[name]

    def justify(self, lyric_text):
        for i in lyric_text:
            if i == '':
                lyric_text.remove(i)
        i = 2
        j = len(lyric_text)+1
        while i <= j:
            lyric_text.insert(i, '')
            j += 1
            i += 3
        lyric_text_bl = '\n'.join(e for e in lyric_text)
        lyric_justified = textile.textile(lyric_text_bl).replace\
            ('<p>', '<p style="text-align: center;">').replace\
            ('">', '"><br />').replace("\t", "    ")
        bs_lyric = BeautifulSoup(lyric_justified, 'html.parser')
        lyric = bs_lyric.prettify()
        return lyric

    def pinglish_to_persian(self, pinglish):
        url = 'http://syavash.com/portal/modules/pinglish2farsi/convertor.php?lang=en'
        data = {'pinglish': pinglish, 'action': 'convert'}
        response = requests.post(url, data)
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.text

    def login(self):
        print('Signing in to Lyricsy.ir...')
        lyricsy_login_address = 'http://lyricsy.ir/wp-admin/'
        self.browser.get(lyricsy_login_address)
        username = self.browser.find_element_by_id("user_login")
        password = self.browser.find_element_by_id("user_pass")
        username.send_keys("hak")
        password.send_keys("123456**123456*")
        self.browser.find_element_by_name("wp-submit").click()

    def new_post_page(self):
        WebDriverWait(self.browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        lyricsy_newpost_address = "http://lyricsy.ir/wp-admin/post-new.php"
        self.browser.get(lyricsy_newpost_address)

    def fill_and_submit(self, title, lyric, cover_link, category_id, tags):
        # Title
        wait = WebDriverWait(self.browser, 10)
        wait.until(EC.presence_of_element_located((By.NAME, 'post_title'))).click()
        self.browser.find_element_by_name('post_title').send_keys(title)
        # HTML
        self.browser.find_element_by_id('content-html').click()
        html_field = self.browser.find_element_by_id('content')
        html_field.click()
        html_field.send_keys(lyric)
        # Justify
        self.browser.find_element_by_id('content-tmce').click()
        # Check-box
        # self.browser.find_elements_by_xpath('//*[@id="{}"]'.format(category_id))
        self.browser.find_element_by_id(category_id).click()
        # Cover Link
        cover_link_field = self.browser.find_element_by_id('acf-field-thumbnail')
        cover_link_field.click()
        cover_link_field.send_keys(cover_link)
        # Album Name
        album_name_field = self.browser.find_element_by_id('acf-field-album')
        album_name_field.click()
        album_name_field.send_keys('تک آهنگ')
        # Tags
        self.browser.find_element_by_id('new-tag-post_tag').click()
        self.browser.find_element_by_id('new-tag-post_tag').send_keys(tags)
        # Source
        source_field = self.browser.find_element_by_id('acf-field-source')
        source_field.click()
        source_field.clear()
        source_field.send_keys('رادیو جوان')
        # Abstract
        abstract_field = self.browser.find_element_by_id('excerpt')
        abstract_field.click()
        abstract_field.send_keys('متن و تفسیر آهنگ')
        abstract_field.send_keys(Keys.ENTER)
        abstract_field.send_keys(title)
        # SEO
        seo_field = self.browser.find_element_by_xpath('//*[@id="aiosp_title_wrapper"]/div/span[2]/div[1]/input[1]')
        seo_field.click()
        seo_field.send_keys('تفسیر و متن اهنگ ', title)
        # Publish
        publish = self.browser.find_element_by_id('post-preview')
        ActionChains(self.browser).move_to_element(publish).perform()
        self.browser.find_element_by_id('publish').click()


def main():
    run = RadioJavanScraping()
    run.login()
    html = run.download()
    # global artist_name
    artist_name = input("Enter Artist/Band Name: ")
    category_id = run.check_box_id(artist_name)
    soup = BeautifulSoup(html, "html.parser")
    block_containers = soup.findAll('a', {'class': 'block_container'})
    for block_container in block_containers:
        # Get Song Link
        link = "https://www.radiojavan.com" + block_container.attrs['href']
        song_link = requests.get(link)
        soup_song_link = BeautifulSoup(song_link.content, 'html.parser')
        # Lyric
        lyric_text = soup_song_link.find('textarea')
        if lyric_text.text is None or lyric_text.text is '':
            print('No Lyric!')
            continue
        lyric_text = lyric_text.text.splitlines()
        justified_lyric = run.justify(lyric_text)
        # Cover Link
        cover_link = soup_song_link.find('div', {'class': 'block_container'}).img['src']
        song_name = run.pinglish_to_persian(block_container.find('span', {'class': 'song_name'}).text)
        song_title = artist_name + " - " + song_name
        # Tags
        with open(os.path.realpath('tags'), 'r') as file:
            tags_file = file.read()
        tags = tags_file.replace('لیریکسی', song_title)
        run.new_post_page()
        run.fill_and_submit(song_title, justified_lyric, cover_link, category_id=category_id, tags=tags)
        print(song_title, 'published')

    print('Finished.')
    RadioJavanScraping.browser.quit()
    sys.exit(0)


if __name__ == '__main__':
    main()
