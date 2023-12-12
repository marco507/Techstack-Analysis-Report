import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from Wappalyzer import Wappalyzer, WebPage
import fire

class Scraper():

    def __init__(self):
        self.debug = False
        self.wappalyzer = Wappalyzer.latest()

    def scrape(self, url):
        success = False
        while not success:
 
            request_url = f'https://api.rocketscrape.com/?apiKey=b190aa9e-ed41-4314-bf92-f694807f50b6&url={url}'
            html = requests.get(request_url)
            
            if html.status_code == 200:
                if self.debug:
                    print('Status Code 200')
                success = True
            
            elif html.status_code == 404:
                print('Status Code 404 - Skipping site')
                success = True

            elif html.status_code == 400:
                if self.debug:
                    print('Status Code 400')
                continue
                
            elif html.status_code == 500:
                if self.debug:
                    print('Status Code 500')
                continue
                
        return html
    
    def scrape_branch(self, branch, branch_link, websites=0, pagination=1, limit=1000):
        
        while websites <= limit:
            
            print(f'Scraping page {pagination}')
            
            url = branch_link + '/' + str(pagination)

            # Retrieve all links from the page
            html = self.scrape(url)
                                
            # Get the links of the current page
            soup = BeautifulSoup(html.content, 'html.parser')
            links = soup.find_all('a', itemprop='url')
            links = [link['href'] for link in links]
            
            # Get the website urls
            for link in tqdm(links[4:]):
                html = self.scrape(link)
                soup = BeautifulSoup(html.content, 'html.parser')
                website_link = soup.find('a', itemprop='url')

                # Scrape the techstack if we have a link
                if website_link:
                    website_link = website_link['href']

                    if not 'firmenabc' in website_link:
                        try:
                            webpage = WebPage.new_from_url(website_link)
                            stack = self.wappalyzer.analyze(webpage) 

                            with open(f'Data/Techstacks/{branch}.csv', 'a') as f:
                                f.write(';'.join([website_link, branch, str(stack)]))
                                f.write('\n')
                            websites += 1
                                    
                        except:
                            continue
                    
            pagination += 1


if __name__ == '__main__':
    fire.Fire(Scraper)
    