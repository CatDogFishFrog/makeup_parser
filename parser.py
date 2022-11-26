import requests
from bs4 import BeautifulSoup

headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.991'}

def get_usd()->float:
    url = 'https://obmennovosti.info/city.php?city=45'
    responce = requests.get(url, headers= headers)
    soup = BeautifulSoup(responce.text, 'lxml')
    data = soup.find_all('script')
    index_start = str(data[-1]).find('"USD","quoted":"UAH","bid":')+44
    index_end = index_start+7
    return float(str(data[-1])[index_start:index_end])

def parse_makeup(url):
    product = {'name':None, 'url':None, 'positions':[]}
    product['url'] = url
    responce = requests.get(url, headers=headers)
    soup = BeautifulSoup(responce.text, 'lxml')
    data = soup.find('div', class_='product-item__buy')
    data1 = data.find_all('div', class_='variant')
    
    product['name'] = soup.find('span', class_='product-item__name').text
    
    for i in data1:
        position = {}
        position['title'] = i.get('title')
        position['eu'] = i.find('i', class_='eu rus') != None
        position['price'] = int(i.get('data-price'))
        product['positions'].append(position)
        
    return product

