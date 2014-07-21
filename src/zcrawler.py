#coding:utf-8

__author__="haowu"
__date__ ="$Jul 15, 2014 4:35:27 PM$"

from ghost import Ghost
import urllib2 
import json
#import simplejson
import time
import MySQLdb
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import socket
import re

class priceHotel:        
    def __init__(self, packageId, lowestPrice, targetUrl, targetSite):
        self.packageId = packageId
        self.lowestPrice = lowestPrice
        self.targetUrl = targetUrl
        self.targetSite = targetSite
        
class zCrawler:    
    """
    main class for the crawler
    """
    def __init__(self):        
        self.hotelList = []
        self.ghost = Ghost()
        self.ghost.wait_timeout = 180
        print 'Ghost.wait_timeout:' , self.ghost.wait_timeout        
        
    def setDates(self, checkIn, checkOut):
        self.checkIn = checkIn
        self.checkOut = checkOut
        return 0
    
    def setRootUrl(self, rootUrlName):
        if(rootUrlName == 'ctrip'):
            self.rootUrl = 'http://hotels.ctrip.com/'
        return 0
    
    def getPriceRegex(self,text):
        #testReg = 'UID=&page_id=102104&VERSION=1&Country=Ó¡¶ÈÄáÎ÷ÑÇ&From=°ÍÀåµº&FromTime=2014-08-10&ToTime=2014-08-12&Star=5&Price=1683&HotelName=AYANA%20Resort%20and%20Spa%20Bali(%e5%b7%b4%e5%8e%98%e5%b2%9b%e9%98%bf%e9%9b%85%e5%a8%9c%e6%b0%b4%e7%96%97%e5%ba%a6%e5%81%87%e9%85%92%e5%ba%97)&CityId=723"'
        reg = ur"&Price=\d+"
        result = re.findall(reg,text) 
        #print type(str(result))
        regDig = ur"\d+"
        result = re.findall(regDig,str(result)) 
        print result[0]
        return result[0]
        
    def getHotels(self):
        db = MySQLdb.connect(db='zanadu_db',host='127.0.0.1',user='root',passwd='',charset='utf8')
        #db.select_db('python')
        #cur = db.cursor()
        cur = db.cursor (cursorclass = MySQLdb.cursors.DictCursor)        
        #sqlWhere = ' WHERE p.id IN (18,19,20) '
        #sqlWhere = ' WHERE p.id IN (18,36,461,403) '
        sqlWhere = ' WHERE p.id IN (18) '
        cur.execute('SELECT p.id, p.name_en, p.name_cn, pm.city  FROM package as p LEFT JOIN package_meta as pm ON p.id = pm.package_id '+ sqlWhere +' LIMIT 10;')
        for data in cur.fetchall():
            #print type(data)
            #print data
            self.hotelList.append(data);
                            
        return 0
    
    def getLowestPrice(self,html):
        priceSelectorJs = """(function () {
                        var element = document.querySelector(".map_mark_price span").textContent;               
                        return element;
                    })();"""

        result, resources = self.ghost.evaluate(priceSelectorJs);
        return result
    
    def getLowestPriceFromDetail(self,html):                
        #http://hotels.ctrip.com/international/14540.html?CheckIn=2014-08-04&CheckOut=2014-08-05&Rooms=1
        # get their hotel id
        hotelIdSelectorJs = """(function () {
                        var element = document.querySelector('.hotel_list_item').id
                        return element;
                    })();"""        
        hotelId, resources = self.ghost.evaluate(hotelIdSelectorJs);                
        #print hotelId, self.checkIn, self.checkOut
        # generate hotel page url
        detailPageUrl = self.rootUrl + 'international/' + str(hotelId) + '.html?CheckIn=' + self.checkIn + '&CheckOut=' + self.checkOut + '&Rooms=1'
        print detailPageUrl
        
        # goto hotel detail page with params using GET
        pageDetail, resources = self.ghost.open(detailPageUrl)
        
        # wait for detail_price
        self.ghost.wait_for_selector('#detail_price dfn')
        
        #  &Price=1683&
        return self.getPriceRegex(self.ghost.content)
                    
    def crackCtrip(self,hotel):        
        # getting ctrip's location id from their API                
        urlApi = self.rootUrl + 'international/Tool/cityFilter_J.ashx?IsUseNewStyle=T&keyword='+hotel['city']
        urlData = urllib2.urlopen(urlApi)          
        urlDataStr = urlData.read()  
        #print type(urlDataStr)         
        a = urlDataStr.split('@')   
        #print type(a)
        #print unicode(a[1],'utf-8')
        for b in a:
            b = unicode(b,'utf-8')
        #a[1] = a[1].encode('gbk')
        del a[0]
        del a[-1]
        #print a[0]
        c = a[0].split('|')
        #print c
        #print c[3]
        #print c[4]        
                  
        locationName = c[4]
        locationId = c[3]
        hotelName = hotel['name_en']
        urlIntl = self.rootUrl + 'international/'+str(locationName)+str(locationId)+'/k2'+hotelName
        #print urlIntl
        
        
        #urlIntl = 'http://hotels.ctrip.com/international/'
        #urlIntl = 'http://english.ctrip.com/hotels/#ctm_ref=nb_hl_top'
        #urlIntl = 'http://english.ctrip.com/hotels/list?city=723&checkin=08-01-2014&checkout=08-02-2014&hotelname=AYANA%20Resort%20and%20Spa'
        #urlIntl = 'http://english.ctrip.com/hotels/list?city=723&checkin=07-18-2014&checkout=07-26-2014&hotelname=AYANA%20Resort%20and%20Spa&searchboxArg=t&optionId=723&optionType=globalhotel_city'
        #urlIntl = 'http://hotels.ctrip.com/international/bali723/k2AYANA%20Resort%20and%20Spa'        
        
        page, resources = self.ghost.open(urlIntl)
        
        #jsCity = 'document.getElementById("txtCity")._lastvalue="Bali"';
        #self.ghost.set_field_value("input[name=cityName]", hotel['city'])
        #self.ghost.set_field_value("input[id=hotelsCity]", "Bali, Indonesia")
        #self.ghost.set_field_value("input[id=hotelsCityHidden]", "723")
        #self.ghost.set_field_value("input[id=optionId]", "723")
        #self.ghost.set_field_value("input[id=optionType]", "globalhotel_city")      
        #self.ghost.set_field_value("input[id=lat]", "-8.409518")  
        #self.ghost.set_field_value("input[id=lon]", "115.18892")  
        #self.ghost.set_field_value("input[id=displayValue]", "Bali, Indonesia")
        #self.ghost.evaluate(jsCity);        
        #self.ghost.set_field_value("input[name=txtCity]", hotel['city'])
        #self.ghost.set_field_value("input[name=cityName]", "°ÍÀåµº", False )        
        
        #self.ghost.set_field_value("input[name=checkIn]", checkIn)
        #self.ghost.set_field_value("input[id=txtCheckIn]", checkIn)
        #self.ghost.set_field_value("input[name=StartTime]", checkIn)
        
        #self.ghost.set_field_value("input[name=checkOut]", checkOut)
        #self.ghost.set_field_value("input[id=txtCheckOut]", checkOut)
        #self.ghost.set_field_value("input[name=DepTime]", checkOut)        
        
        #self.ghost.set_field_value("input[id=txtHotelNameKeyWords]", hotel['name_en'])
        #self.ghost.set_field_value("input[name=keywordNew]", hotel['name_en'])
        #self.ghost.set_field_value("input[name=txtKeyword]", hotel['name_en'])
        
        #self.ghost.fire_on("listForm", "submit", expect_loading=True)
        #self.ghost.fire_on("J_searchForm", "submit", expect_loading=True)
        #self.ghost.click("#btnSearch_SearchBox")        
        #self.ghost.wait_for_selector('.hotel_list_item')
        
        '''
        self.ghost.sleep(5)
        lowestPrice = self.getLowestPrice(self.ghost.content)        
        print lowestPrice
        '''
        
        lowestPrice = self.getLowestPriceFromDetail(self.ghost.content)        
        print lowestPrice
        
        #priceHotel = priceHotel(hotel['id'],lowestPrice,urlIntl,'ctrip')
        priceHotel = {
            'package_id': hotel['id'],
            'lowest_price' : lowestPrice,
            'target_site' : 'ctrip',
            'target_url' : urlIntl,
        }
        print priceHotel
        
        pageContent = self.ghost.content
        fileName = "testwhctripDetails_"+str(hotel['id'])+".html"
        fp = open(fileName,'w')
        fp.write(pageContent)
        fp.close()
        
        
        return 0
    

if __name__ == "__main__":    
        
    checkIn = '2014-08-10'
    checkOut = '2014-08-12'
    print "zCrawlerStart"
    timeStart = time.time()
    
    ### print ip ###
    #localIP = socket.gethostbyname(socket.gethostname())#µÃµ½±¾µØip
    #print (localIP)
    ipList = socket.gethostbyname_ex(socket.gethostname())
    #for i in ipList:
    print ipList
        #if i != localIP:
           #print (i,end=',')
    
    
    #init
    crawler = zCrawler()    
    
    # get list of hotel
    crawler.getHotels()
    
    # set checkin/out dates
    crawler.setDates(checkIn, checkOut)
    
    # set root url
    crawler.setRootUrl('ctrip')
    
    print crawler.hotelList
    
    
    #exit(0)
    # start getting lowest price for each hotel 
    for hotel in crawler.hotelList:        
        crawler.crackCtrip(hotel)
        time.sleep(1)
    
    
    
    
    print "Done...TimeElaspsed:",time.time()-timeStart


