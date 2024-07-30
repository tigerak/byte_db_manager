from bs4 import BeautifulSoup as bs
import urllib3
from urllib3.util.ssl_ import create_urllib3_context
import ssl
import re
# pip install pyOpenSSL

class Scraping():
    def __init__(self):
        self.ctx = create_urllib3_context()
        self.ctx.load_default_certs()
        self.ctx.options |= 0x4 # ssl.OP_LEGACY_SERVER_CONNECT
        
    def scraping(self, input_url):
        with urllib3.PoolManager(ssl_context=self.ctx) as http:
            try:
                response = http.request("GET", input_url)
            except:
                try:
                    response = http.request("GET", input_url)
                except:
                    media = '알 수 없는 언론사'
                    title = '주소가 없군요.'
                    article = '''
                            주소를 입력하지 않았습니다.
                            문제가 반복된다면 담당자에게 이야기 해주세요.
                            기사 주소를 입력하세요.
                        '''
                    article_date = '날씨 : 맑음'
                    return media, title, article, article_date
            
        soup = bs(response.data, 'html.parser')
        
        # print(response.headers)
        # print(response.data.decode('utf-8')[:500])
        # print(response.status)
        
        # 연합 or 이투데이
        if (input_url.find('yna') != -1) or (input_url.find('etoday') != -1):
            real_url = input_url
        else:
            try:
                # <head> 태그 내의 모든 <link> 태그 찾기
                links = soup.head.find_all('link')
                # 각 <link> 태그의 href 속성 값 추출
                real_url = links[0].get('href')
            except:
                real_url = None
        
        try:
            if real_url.find('yna') != -1:
                media = '연합뉴스' 
                title, article, article_date = self._yna(soup)
                
            elif real_url.find('etoday') != -1:
                media = '이투데이' 
                title, article, article_date = self._etoday(soup)
                
            else :
                media = '알 수 없는 언론사'
                title = input_url
                article = real_url
                article_date = '날씨 : 맑음'
            
            # article과 article_date의 \n 제거.
            article = article.replace("\n", "")
            article_date = article_date.replace("\n", "")
            
            # print(f'''
            #     제목 :\n{title} \n
            #     기사 :\n{article}\n
            #     날짜 :\n{article_date}
            #     ''')

            return media, title, article, article_date
        
        except:
            print(input_url, '<==> [REAL URL] :', real_url)
            media = '알 수 없는 언론사'
            title = '주소를 확인해보세요.'
            article = '지원하지 않는 형식의 뉴스 페이지입니다.\n담당자에게 이야기 해주세요.'
            article_date = '날씨 : 맑음'
            return media, title, article, article_date
            
        
    def _get_real_url(self, response):
        real_url = response.geturl()
        return real_url
        
    def _yna(self, soup):
        # 제목 및 기사 수집
        title = ''
        article_list = []
        # PC version.
        title_list = soup.select('#articleWrap > div.content03 > header > h1')
        # 테이블 제거 후 추출
        #articleWrap > div.content01.scroll-article-zone01 > div > div > article > table
        tables = soup.select('table')
        
        for table in tables:
            table.decompose()
        paragraph_list = soup.select('#articleWrap > div.content01.scroll-article-zone01 > div > div > article > p')
        if paragraph_list == []:
            # Mobile version.
            title_list = soup.select('#articleWrap > header > h1')
            paragraph_list = soup.select('#articleWrap > div > p')
        
        # HTML 제거
        for t in title_list:
            title = title.join(t.get_text())
        for p in paragraph_list:
            article_list.append(p.get_text())
        
        # 연합뉴스 기자명 제거
        if article_list[0].find(' = ') != -1:
            article_list[0] = article_list[0].split(' = ')[1]
        
        article = ''.join(article_list[:-2])
            
        # 송고 시간
        date = ''
        date_paragraph = soup.select('#newsUpdateTime01')
        for d in date_paragraph:
            date = date.join(d.get_text())
        article_date = date.replace('송고시간', '')
        
        return title, article, article_date
            
    def _etoday(self, soup):
        # 제목, 기사, 송고시간 수집
        title = ''
        article_list = []
        date = ''
        # PC version.
        title_list = soup.select('body > div.wrap > article > section.news_dtail_view_top_wrap > h1')
        # 테이블 제거 후 추출
        #경로 못 찾음 - 테이블 일단 다 지움.
        tables = soup.select('table')
        for table in tables:
            table.decompose()

        paragraph_list = soup.select('body > div.wrap > article > section.view_body_moduleWrap > div.l_content_module > div > div > div.view_contents > div.articleView > p')
        #date_paragraph = soup.select('body > div.wrap > article > section.news_dtail_view_top_wrap > div.view_top_container > div > span')[0]
        if paragraph_list == []:

            # Mobile version.
            title_list = soup.select('body > div.wrap > div > div.containerWrap > section.DetailView_Wrap.mboxcont > div.view_mtitle > h1')
            paragraph_list = soup.select('#contents_body > p')
            date_paragraph = soup.select('body > div.wrap > div > div.containerWrap > section.DetailView_Wrap.mboxcont > div.view_mtitle > p')[0]
            span_tag = date_paragraph.find('span')
            if span_tag:
                span_tag.decompose()
        else:
            date_paragraph = soup.select('body > div.wrap > article > section.news_dtail_view_top_wrap > div.view_top_container > div > span')[0]

        
        # HTML 제거
        for t in title_list:
            title = title.join(t.get_text())
        for p in paragraph_list:
            # print('@@@ :', p)
            # subview_title 및 img alt 제거
            if ('subview_title' not in str(p)) and (' src=' not in str(p)): # sub title는 따로 있어서 그냥 빼버려도 됨.
                article_list.append(p.get_text())
            elif ' src=' in str(p): # 이미지는 기사 내용 포함되는 경우 있음.
                cleaned_html = re.sub(r'<p>|</p>|<div.*</div>', '', str(p), flags=re.DOTALL)
                article_list.append(cleaned_html)
                # print('### :', cleaned_html)
        
        article = ''.join(article_list)
        
        # 송고 시간
        for d in date_paragraph:
            date = date.join(d.get_text())
        article_date = date.replace('입력 ', '')
        
        return title, article, article_date