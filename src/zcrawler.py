#coding:utf-8

__author__="haowu"
__date__ ="$Jul 15, 2014 4:35:27 PM$"

from ghost import Ghost
import MySQLdb, urllib2, socket, os, sys, time, json, re
reload(sys)
sys.setdefaultencoding('utf-8')

def isset(v):
    """
    check variable is set
    """
    try :  
        type (eval(v))  
    except :  
        return   0   
    else :  
        return   1 

def parseInput(argv):    
    """
    parse input arguments to a dict of params
    """
    inputParams = {}
    for arg in argv:        
        param = arg.split('=')                
        if len(param)>1:
            inputParams[param[0]] = param[1]
    return inputParams


def validateInputParams(inputParams):    
    """
    check required params exist
    """
    if "checkin" not in inputParams:
        print 'missing checkin'
        exit(1)
    if "checkout" not in inputParams:    
        print 'missing checkout'
        exit(1)

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
        
    def savePrice(self, priceHotel):    
        """
        save price of hotel to db
        """
        
        return 0
        
    def setDates(self, checkIn, checkOut):
        """
        set crawler to use checkin/out dates from inputParams
        """
        self.checkIn = checkIn
        self.checkOut = checkOut
        return 0
    
    def setRootUrl(self, rootUrlName):
        """
        set the root url of the target site for current crawler task
        """
        if(rootUrlName == 'ctrip'):
            self.rootUrl = 'http://hotels.ctrip.com/'
            self.targetSite = rootUrlName
        return 0
    
    def getPriceRegex(self,text):
        #testReg = 'UID=&page_id=102104&VERSION=1&Country=印度尼西亚&From=巴厘岛&FromTime=2014-08-10&ToTime=2014-08-12&Star=5&Price=1683&HotelName=AYANA%20Resort%20and%20Spa%20Bali(%e5%b7%b4%e5%8e%98%e5%b2%9b%e9%98%bf%e9%9b%85%e5%a8%9c%e6%b0%b4%e7%96%97%e5%ba%a6%e5%81%87%e9%85%92%e5%ba%97)&CityId=723"'
        reg = ur"&Price=\d+"
        result = re.findall(reg,text) 
        #print type(str(result))
        regDig = ur"\d+"
        result = re.findall(regDig,str(result)) 
        #print result[0]
        return result[0]
        
    def getHotels(self):
        db = MySQLdb.connect(db='zanadu_db',host='127.0.0.1',user='root',passwd='',charset='utf8')
        #db.select_db('python')
        #cur = db.cursor()
        cur = db.cursor (cursorclass = MySQLdb.cursors.DictCursor)        
        #sqlWhere = ' WHERE p.id IN (18,19,20) '
        sqlWhere = ' WHERE p.id IN (18,36,461,403) '
        #sqlWhere = ' WHERE p.id IN (18) '
        cur.execute('SELECT p.id, p.name_en, p.name_cn, pm.city  FROM package as p LEFT JOIN package_meta as pm ON p.id = pm.package_id '+ sqlWhere +' LIMIT 10;')
        for data in cur.fetchall():
            #print type(data)
            #print data
            self.hotelList.append(data);
                            
        return 0
    
    def isNoResult(self,html):
        priceSelectorJs = """(function () {
                        var element = document.querySelector(".search_noresult strong").textContent;               
                        return element;
                    })();"""

        result, resources = self.ghost.evaluate(priceSelectorJs);
        print result
        return result
        
    
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
         
    def getCtripSearchUrl(self):
        #domestic
        #http://hotels.ctrip.com/Domestic/Tool/AjaxIndexCityNew.aspx?keyword=shanghai
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
        #print a[0]`1
        c = a[0].split('|')
        #print c
        #print c[3]
        #print c[4]        
                  
        locationName = c[4]
        locationId = c[3]
        hotelName = hotel['name_en']
        return self.rootUrl + 'international/'+str(locationName)+str(locationId)+'/k2'+hotelName
                    
    def crackCtrip(self,hotel):        
        # get the url for searching a hotel
        urlSearch = self.getCtripSearchUrl
        #print urlIntl
        

        
        page, resources = self.ghost.open(urlIntl)

        
        '''
        self.ghost.sleep(5)
        lowestPrice = self.getLowestPrice(self.ghost.content)        
        print lowestPrice
        '''
        
        noResultFlag = self.isNoResult(self.ghost.content)
        if(noResultFlag == None):
            lowestPrice = self.getLowestPriceFromDetail(self.ghost.content)        
        else:
            lowestPrice = 'hotel no found in ' + self.targetSite
        
        #print lowestPrice
        
        #priceHotel = priceHotel(hotel['id'],lowestPrice,urlIntl,'ctrip')
        priceHotel = {
            'package_id': hotel['id'],
            'lowest_price' : lowestPrice,
            'target_site' : 'ctrip',
            'target_url' : urlSearch,
            'check_in' : self.checkIn,
            'check_out' : self.checkOut,
        }
        print priceHotel
        self.savePrice(priceHotel)
        
        pageContent = self.ghost.content
        fileName = "testwhctripDetails_"+str(hotel['id'])+".html"
        fp = open(fileName,'w')
        fp.write(pageContent)
        fp.close()
        
        
        return 0
    
    def crackQunar(self):
        return 0

"""
main()
"""
if __name__ == "__main__":      
    inputParams = parseInput(sys.argv)
    print "inputParams:",inputParams        
    validateInputParams(inputParams)
    print "zCrawlerStart"
    
    timeStart = time.time()
        
    ### print ip ###
    #localIP = socket.gethostbyname(socket.gethostname())#得到本地ip
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
    crawler.setDates(inputParams['checkin'], inputParams['checkout'])
    
    # set root url
    crawler.setRootUrl('ctrip')
    
    print crawler.hotelList
    
    
    #exit(0)
    # start getting lowest price for each hotel 
    for hotel in crawler.hotelList:        
        crawler.crackCtrip(hotel)
        time.sleep(1)
    
    
    
    
    print "Done...TimeElaspsed:",time.time()-timeStart


