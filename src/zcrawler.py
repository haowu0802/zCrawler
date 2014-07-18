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

class zCrawler:    
    """
    main class for the crawler
    """
    def __init__(self):        
        self.hotelList = []
        self.ghost = Ghost()
        self.ghost.wait_timeout = 120
        print 'Ghost.wait_timeout:' , self.ghost.wait_timeout
    def getHotels(self):
        db = MySQLdb.connect(db='zanadu_db',host='127.0.0.1',user='root',passwd='',charset='utf8')
        #db.select_db('python')
        #cur = db.cursor()
        cur = db.cursor (cursorclass = MySQLdb.cursors.DictCursor)        
        sqlWhere = ' WHERE p.id IN (18,19,20) '
        #sqlWhere = ' WHERE p.id IN (18) '
        cur.execute('SELECT p.id, p.name_en, p.name_cn, pm.city  FROM package as p LEFT JOIN package_meta as pm ON p.id = pm.package_id '+ sqlWhere +' LIMIT 10;')
        for data in cur.fetchall():
            #print type(data)
            #print data
            self.hotelList.append(data);
                            
        return 0
    def test(self,hotel):
        checkIn = '2014-08-01'
        checkOut = '2014-08-02'
        #print type(hotel)
        print hotel
        
        urlApi = 'http://hotels.ctrip.com/international/Tool/cityFilter_J.ashx?IsUseNewStyle=T&keyword='+hotel['city']
        urlData = urllib2.urlopen(urlApi)          
        urlDataStr = urlData.read()  
        print type(urlDataStr)         
        a = urlDataStr.split('@')
        print type(a)
        #print unicode(a[1],'utf-8')
        for b in a:
            b = unicode(b,'utf-8')
        #a[1] = a[1].encode('gbk')
        del a[0]
        del a[-1]
        print a[0]
        c = a[0].split('|')
        print c
        print c[3]
        print c[4]
        #resApi = simplejson.loads(a[1])
        #resApi = json.loads(a[1])        
        #print resApi
        locationName = c[4]
        locationId = c[3]
        hotelName = hotel['name_en']
        urlIntl = 'http://hotels.ctrip.com/international/'+locationName+locationId+'/k2'+hotelName
        print urlIntl
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
        #self.ghost.set_field_value("input[name=cityName]", "∞Õ¿Âµ∫", False )        
        
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
        #self.ghost.sleep(5)
        #self.ghost.wait_for_selector('.hotel_list_item')
        
        
        pageContent = self.ghost.content
        fileName = "testwhctrip_"+str(hotel['id'])+".html"
        fp = open(fileName,'w')
        fp.write(pageContent)
        fp.close()
        
        return 0
    

if __name__ == "__main__":    
    print "zCrawlerStart"
    timeStart = time.time()
    
    crawler = zCrawler()    
    # get list of hotel
    crawler.getHotels()
    print crawler.hotelList
    
    for hotel in crawler.hotelList:        
        crawler.test(hotel)
    
    
    
    time.sleep(1)
    print "Done...TimeElaspsed:",time.time()-timeStart


