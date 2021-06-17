# E-HDown, an E-hentai.org gallery downloader and organizer.
# Copyright (C) 2021  Liquorice10113.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

try:
    from bs4 import BeautifulSoup
except:
    print("BeautifulSoup not found, try 'pip install beautifulsoup4'.")
    quit()

import requests as req
import re,os,json,sys
import time,math,random

ehconfigTemplate= '''folderDir = "./COMIC/"
headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36'
}
proxies = {
    'http':'127.0.0.1:8080',
    'https':'127.0.0.1:8080'
}
proxies = None'''


if not os.path.exists("configeh.py"):
    with open("configeh.py" ,'w') as f:
        f.write(ehconfigTemplate)
    print("Config file created.")
    print("Quiting...")
    quit()
        
from configeh import *

class Cookies(dict):
    def __init__(self):
        return
    def load(self,f):
        with open(f,'r') as fh:
            jsonC = json.load(fh)
            for i in jsonC:
                self[i['name']] = i['value']  

ehcookies = Cookies()
if os.path.exists("./cookies.json"):
    ehcookies.load("./cookies.json")

def sw(s,c="none",h=False):
    colors = {"red":31,"green":32,"yellow":33,"blue":34,"none":0}
    s = str(s)
    if os.name=="posix":
        if h:
            s =  "\033[1m" + s
        s = "\033[{0}m".format(colors[c]) + s
        s = s + "\033[0m"
    return s


def fetch(url,binary=False):
    global ehcookies
    #print(url)
    if "509.gif" in url:
        print(sw("Limits reached maybe?",c="yellow"))
        getLimitsInfo()
        if input("Continue?[y/n]") == 'n':
            raise Exception("Limits reached.")
    rc = 1
    while True:
        try:
            content = req.get(url,headers=headers,cookies = ehcookies,proxies=proxies)
            cookies = content.cookies
            if binary:
                return content.content
            else:
                return content.text
        except KeyboardInterrupt:
            print(sw('[KeyboardInterrupt]',c="yellow"))
            raise
        except Exception as e:
            print(e)
            if rc>6: 
                #raise Exception("Download Failed.")
                print(sw('Failed after 6 attemps.',c="red"))
                return b''
            time.sleep(5)
            print(sw('[Retrying]',c="yellow"))
            rc += 1

def wash(s):
    for i in "\/:*?\"<>|": 
        s = s.replace(i,'')
    return s

def uniCnt(cnt):
    return (3-len(str(cnt)))*'0'+str(cnt)

            
class Meta(dict):
    def __init__(self):
        self['length'] = 0
        return
    
    def load(self,f):
        with open(f,'r') as fh:
            jsonC = json.load(fh)
            for i in jsonC:
                self[i] = jsonC[i]
            if not self['length'] == 0:
                if 'pages' in self:
                    self['length'] = int(self['pages'])
                
    def dump(self,f):
        with open(f,'w') as fh:
            json.dump(self,fh)

class Gallery():
    def __init__(self, url, indexEnabled, mute=False):
        self.pages = []
        self.url = url
        self.html = ''
        self.actualCnt = 0
        self.mute = mute
        self.indexEnabled = indexEnabled
        self.meta = Meta()
        self.errored = False
        self.folderName = None
        print("INDEX PREFIX {0}".format(sw("ENABLED",c="green") if indexEnabled else "DISABLED"))
        return
    
    def parse(self,folderName=None):
        try:
            if not self.mute: print("Parsing...")

            self.html = fetch(self.url)
            if "This gallery has been removed or is unavailable" in self.html:
                self.errored = True
                print(sw("This gallery has been removed or is unavailable.",c="red"))
                return
            soup = BeautifulSoup(self.html,'html.parser')
            self.title = wash(soup.title.text.replace(' - E-Hentai Galleries',''))

            if folderName:
                self.folderName = folderName
                if self.folderName != self.title:
                    print(sw("Folder name dosent match title.",c="yellow"))
                    print("Changing\n",self.folderName,"\nto\n",self.title)
                    os.rename(folderDir+self.folderName,folderDir+self.title)

            if "There are newer versions of this gallery available" in self.html:
                print(sw("There are newer versions of this gallery available.",c="yellow"))
                print(sw("Hold on...",c="yellow"))
                new_url = soup.find(id="gnd").find_all("a")[-1].attrs["href"]
                print(sw("Url changed from:\n"+self.url+"\nto:\n"+new_url,c="yellow"))
                self.url = new_url
                self.html = fetch(self.url)
                soup = BeautifulSoup(self.html,'html.parser')
                new_title = wash(soup.title.text.replace(' - E-Hentai Galleries',''))
                if self.title != new_title:
                    print(sw("Title changed from:\n"+self.title+"\nto:\n"+new_title,c="yellow"))
                    try:
                        if os.path.exists(folderDir+self.title):
                            os.rename(folderDir+self.title,folderDir+new_title)
                    except:
                        print(sw("Failed to change folder name! Needs attention.",c="red"))
                        self.errored = True
                        return
                    self.title = new_title
            
            soup = BeautifulSoup(self.html,'html.parser')
            #print(self.html)
            self.length = int(re.search('(\d+) pages',self.html).group(1))
            #self.title = wash(soup.title.text.replace(' - E-Hentai Galleries',''))
            if not self.mute: print(sw(self.title,h=True))
            
            #Setup meta data.
            if not os.path.exists(folderDir+self.title):
                os.mkdir(folderDir+self.title)
            if os.path.exists(folderDir+self.title+'/meta.json'):
                #print("Meta found.")
                self.meta.load(folderDir+self.title+'/meta.json')
                if  not 'indexEnabled' in self.meta:
                    self.meta['indexEnabled'] = self.indexEnabled
                else:
                    self.indexEnabled = self.meta['indexEnabled']
                    print("META.JSON: INDEX PREFIX {0}".format(sw("ENABLED",c="green") if self.indexEnabled else "DISABLED"))
            else:
                self.meta['indexEnabled'] = self.indexEnabled
            
            #file_names = []
            pageUrls = soup.find(class_="ptt").find_all('a')
            pageUrls = [ u.attrs['href'] for u in pageUrls ]
            pageUrls = sorted( list(set(pageUrls)) )
            for galleryPageUrl in pageUrls:
                self.html  = fetch(galleryPageUrl)
                soup = BeautifulSoup(self.html,'html.parser')
                
                for div in soup.find_all('div', class_='gdtm'):
                    index_ = uniCnt(int(div.div.a.img.attrs['alt'])-1)
                    name = re.match('Page \d+: (.+)',div.div.a.img.attrs['title']).group(1)
                    pageUrl = div.div.a.attrs['href']
                    #print(pageUrl)
                    page = Page(self.title,name,pageUrl,index_,self.indexEnabled)
                    #file_names.append(page.name)
                    if not page.exists: self.actualCnt += 1
                    self.pages.append(page)
                    
            print(sw("Parsing completed, {0} images found, {1} to download.".format(len(self.pages),self.actualCnt),h=True))
            #self.meta['file_names'] = file_names
            self.meta['url'] = self.url
            self.meta['finished'] = False
            self.meta['length'] = len(self.pages)
            self.meta.dump(folderDir+self.title+'/meta.json')
        except Exception as e:
            #raise
            print(e)
            print(sw("Parse failed for:\n"+self.url,c="red"))
            self.errored = True

    def download(self):
        cnt = 1
        fin = 0
        if len(self.pages) == 0:
            print("No images found.")
            return
        if not self.mute: print("Starting...")
        for page in self.pages:
            if not page.exists:
                print("[{0}/{1}] {2}...".format(cnt,len(self.pages),page.name),end=' ')
                sys.stdout.flush()
                page.parse()
                page.download()
                if not page.errored:
                    print('Done.')
                else:
                    self.errored = True
                fin += 1
            else:
                if not self.mute: print("[{0}/{1}] {2} skiped.".format(cnt,len(self.pages),page.name))
            cnt +=1
        print('Completed, {0} images downloaded.'.format(fin))
        
        ongoing = False
        for i in ['wip','ongoing','on going','artwork','in progress','inprogress','incomplete']:
            if i in self.title.lower():
                print("Flaged as on going.")
                ongoing = True
                break
        if not ongoing:
            if not self.errored:
                self.meta['finished'] = True
            else:
                print(sw("Failed to fetch one or more images.",c="yellow"))
        self.meta.dump(folderDir+self.title+'/meta.json')           

class Page(dict):
    def __init__(self,title,name,url,index_,indexEnabled):
        self.title = title
        self.name = name.replace(".PNG",'.png').replace(".GIF",'.gif').replace(".JPEG",'.jpg').replace(".BMP",'.bmp').replace(".JPG",'.jpg')
        self.url = url
        self.index_ = index_
        self.indexEnabled = indexEnabled
        self.exists = False
        self.errored = False
        if self.indexEnabled:
            if  os.path.exists(folderDir+self.title+'/'+self.index_+'_'+self.name):
                self.exists = True
            self.name = self.index_+'_'+self.name
        else:
            if os.path.exists(folderDir+self.title+'/'+self.name) or os.path.exists(folderDir+self.title+'/'+self.index_+'_'+self.name):
                self.exists = True
        return

    def parse(self):
        if self.exists:
            return
        self.html = fetch(self.url)
        soup = BeautifulSoup(self.html,"html.parser")
        self.imgurl = soup.find(id="img").attrs["src"]

    def download(self):
        if self.exists:
            return
        imgbin = fetch(self.imgurl,True)
        print(int(len(imgbin)/1024),"KB",end=" ",sep="")
        if len(imgbin)<1024:
            print(sw("No data fetched.\nSkip for now.",c="red"))
            self.errored = True
            return
        with open(folderDir+self.title+'/'+self.name,'wb') as f:
            f.write(imgbin)

def getLimitsInfo():
    global ehcookies
    if not ehcookies:
        print("No cookies found!")
        return
    html = fetch('https://e-hentai.org/home.php')
    res = re.search("You are currently at .strong.(\d+)..strong. towards a limit of .strong.(\d+)..strong.\.",html)
    current = int(res.group(1))
    limit = int(res.group(2))
    print("[Limits {0}/{1}, {2} hours {3} minutes utill fully regenerated]".format(current,limit,int(current/60/3),int(current/3)%60 ))
    if current > limit:
        print('[{0} minutes utill ready for next download]'.format( int((current-limit)/3) ))

def resume(resume_all=False):
    folders = os.listdir(folderDir)
    random.shuffle(folders)
    for i in folders:
        if os.path.exists(folderDir+i+'/meta.json'):
            m = Meta()
            m.load(folderDir+i+'/meta.json')
            if  m['finished'] and not resume_all:
                continue
            print(50*'-')
            print('RESUME',sw(i,h=True))
            if  not 'indexEnabled' in m:
                m['indexEnabled'] = False
            g = Gallery(m['url'],m['indexEnabled'],True)
            g.parse(i)
            if g.errored:
                continue
            if g.title != i and os.path.exists(folderDir+i):
                print(sw("Wait, gallery title changed?",c="blue"))
                print("Go check",m['url'])
                continue
                if input("Change folder name and continue?[y/n]") == 'y':
                    os.rename(folderDir+i, folderDir+g.title)
                    print("Folder name changed form '{0}' to '{1}'".format(i,g.title))
                    g.parse()
                else:
                    print("Skip for now.")
                    continue
            g.download()

def main():
    print("E-H Downloader.")
    print("PROXIES {0}".format("ENABLED" if proxies else "DISABLED"))
    if proxies: print("PROXIES:\n",proxies)
    #print("INDEX PREFIX {0}".format("ENABLED" if indexEnabled else "DISABLED"))
    getLimitsInfo()
    print("1) ADD")
    print("2) RESUME")
    print("3) ADD (ENABLE INDEX)")
    print("4) RESUME (ALL)")
    #print("5) FROM TEXT FILE")

    indexEnabled = False
    inputString = input(">>")

    if inputString == '1':
        inputString = input("URL>>")
    elif inputString == '2':
        resume()
        return
    elif inputString == '3':
        inputString = input("URL>>")
        indexEnabled = True
    elif inputString == '4':
        resume(True)
        return
    elif inputString == '5':
        txt = input("txt>>")
        urls = open(txt,'r').readlines()
        urls = [ url.replace("\n","") for url in urls if len(url)>2 ]
        for url in urls:
            gallery = Gallery(url,indexEnabled)
            print("Parsing only...")
            gallery.parse()
            if gallery.errored:
                with open("errored.txt",'a') as f:
                    f.write(url+"\n")
            print("OK")
            #gallery.download()

        return
    
    if re.match("http.+",inputString):
        gallery = Gallery(inputString,indexEnabled)
        gallery.parse()
        gallery.download()
    else:
        print("Not a valid URL.")
    
    

main()