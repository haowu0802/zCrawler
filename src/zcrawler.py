#coding:utf-8

__author__="haowu"
__date__ ="$Jul 15, 2014 4:35:27 PM$"

from ghost import Ghost
from datetime import *
import MySQLdb, urllib2, socket, os, sys, time, json, re, csv
reload(sys)
sys.setdefaultencoding('utf-8')

def peek(*p):
    """
    for debuging
    """
    for var in p:
        print var        

def isset(v):
    """
    check variable is set
    """
    try:
        type(eval(v))
    except:
        return 0
    else:
        return 1

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
        """
        
        """
        self.db = MySQLdb.connect(db='zanadu_db',host='127.0.0.1',user='root',passwd='',charset='utf8')        
        #self.cur = self.db.cursor()
        self.cur = self.db.cursor (cursorclass = MySQLdb.cursors.DictCursor)   
        self.queryDate = str(date.today())
        self.hotelList = {}
        self.ghost = Ghost()
        self.ghost.wait_timeout = 60
        print 'Ghost.wait_timeout...' , self.ghost.wait_timeout
        self.rootUrl = {
            'ctrip' : 'http://hotels.ctrip.com/',
            'qunar' : 'http://hotel.qunar.com/',
            'zanadu' : 'http://www.zanadu.cn/'
        }
        
    def resetGhost(self):
        self.ghost.exit()
        self.ghost = Ghost()
        self.ghost.wait_timeout = 60
        
    def savePrice(self, priceHotel):
        #peek('priceHotel',priceHotel);exit(0);
        """
        save price of hotel to db
        """
        insertSql = 'INSERT INTO `crawler_hotel` '
        updateSql = 'UPDATE `crawler_hotel` '
        setSql = 'SET '        
        setUpdateSql = 'SET '
        whereSql = ' WHERE '
        for k,v in priceHotel.iteritems():            
            if(k in ['package_id','name_en','target_url','target_site','lowest_price','query_date','check_in_date','check_out_date']):                
                setSql = setSql + '`' + str(k) + '`' + '=' + '"' + str(v) + '"' + ', '
            
            if (k in ['lowest_price','target_url'])  :
                setUpdateSql = setUpdateSql + '`' + str(k) + '`' + '=' + '"' + str(v) + '"' + ', '
            elif (k in ['package_id','target_site','query_date','check_in_date','check_out_date']) :
                whereSql = whereSql + '`' + str(k) + '`' + '=' + '"' + str(v) + '"' + ' AND '
        whereSql = whereSql.rstrip('AND ')
        insertSql = insertSql + setSql + '`creation_time`=NOW(), `last_update_time`=NOW() '
        updateSql = updateSql + setUpdateSql + '`last_update_time`=NOW() ' + whereSql
                        
        # try to insert, if exist , update , this depends on the columns to be join indexed
        try:            
            insertResult = self.cur.execute(insertSql)                            
            if(insertResult<1):
                peek(insertSql)
                print '[ERROR]insert failed: ',insertResult
        except:            
            updateResult = self.cur.execute(updateSql)                             
            if(updateResult<1):
                peek(updateSql)
                print '[ERROR]update failed: ',updateResult
                
        self.db.commit();        
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
            self.rootUrl = ''
            self.targetSite = rootUrlName
        return 0
    
    def getPriceRegex(self,text):
        """
        
        """
        #testReg = 'UID=&page_id=102104&VERSION=1&Country=Ó¡¶ÈÄáÎ÷ÑÇ&From=°ÍÀåµº&FromTime=2014-08-10&ToTime=2014-08-12&Star=5&Price=1683&HotelName=AYANA%20Resort%20and%20Spa%20Bali(%e5%b7%b4%e5%8e%98%e5%b2%9b%e9%98%bf%e9%9b%85%e5%a8%9c%e6%b0%b4%e7%96%97%e5%ba%a6%e5%81%87%e9%85%92%e5%ba%97)&CityId=723"'
        reg = ur"&Price=\d+"
        result = re.findall(reg,text)        
        regDig = ur"\d+"
        result = re.findall(regDig,str(result))    
        return result[0]
        
    def getHotels(self):
        """
        
        """
        #sqlWhere = ' WHERE p.published = 1 AND p.type = 1 LIMIT 10'
        
        #sqlWhere = ' WHERE p.published = 1 AND p.type = 1 AND p.id IN (36,461,20,403,40,18) '
        sqlWhere = ' WHERE p.published = 1 AND p.type = 1 AND p.id IN (36) '
        # 27 cannot be searched , city not found
        #sqlWhere = ' WHERE p.published = 1 AND p.type = 1 AND p.id IN (32) '
        #sqlWhere = ' WHERE p.published = 1 AND p.type = 1 LIMIT 5 '
        #sqlWhere = ' WHERE p.id IN (18,19,20)  LIMIT 10;'
        #sqlWhere = ' WHERE p.id IN (18,36,461,403)  LIMIT 10;'
        #sqlWhere = ' WHERE p.id IN (18)  LIMIT 10;'
        self.cur.execute('SELECT p.id as package_id, p.name_en, p.name_cn, pm.city, pm.country  FROM package as p LEFT JOIN package_meta as pm ON p.id = pm.package_id '+ sqlWhere )
        for data in self.cur.fetchall():            
            self.hotelList[int(data['package_id'])]=data;        
        return 0
    
    def isNoResult(self,html):
        """
        
        """
        priceSelectorJs = """(function () {
                        var element = document.querySelector(".search_noresult strong").textContent;
                        return element;
                    })();"""
        result, resources = self.ghost.evaluate(priceSelectorJs);
        return result
    
    def getLowestPrice(self,html):
        """
        
        """
        priceSelectorJs = """(function () {
                        var element = document.querySelector(".map_mark_price span").textContent;
                        return element;
                    })();"""
        result, resources = self.ghost.evaluate(priceSelectorJs);
        return result
    
    def getLowestPriceCtrip(self,html):
        """
        
        """
        #http://hotels.ctrip.com/international/14540.html?CheckIn=2014-08-04&CheckOut=2014-08-05&Rooms=1
        # get their hotel id
        hotelIdSelectorJs = """(function () {
                        var element = document.querySelector('.hotel_list_item').id
                        return element;
                    })();"""
        hotelId, resources = self.ghost.evaluate(hotelIdSelectorJs);
        
        if(hotelId == None):            
            return 'NF' # hotel not found
        
        # generate hotel page url
        detailPageUrl = self.rootUrl['ctrip'] + 'international/' + str(hotelId) + '.html?CheckIn=' + self.checkIn + '&CheckOut=' + self.checkOut + '&Rooms=1'        
        
        # goto hotel detail page with params using GET
        pageDetail, resources = self.ghost.open(detailPageUrl)
        
        # wait for detail_price
        try:
            self.ghost.wait_for_selector('#detail_price dfn')
        except Exception,e:
            print '[ERROR]price cannot be found ... ' + str(detailPageUrl)
            print Exception,":",e  
            return 'NP' # lowest price not found, usually no room available for selected date interval
        
        #  &Price=1683&
        return self.getPriceRegex(self.ghost.content)
    
    def getLowestPriceZanadu(self,html):
        """
        
        """
        
        
        #http://hotels.ctrip.com/international/14540.html?CheckIn=2014-08-04&CheckOut=2014-08-05&Rooms=1
        # get their hotel id
        hotelIdSelectorJs = """(function () {
                        var element = document.querySelector('.hotel_list_item').id
                        return element;
                    })();"""
        hotelId, resources = self.ghost.evaluate(hotelIdSelectorJs);
        
        if(hotelId == None):            
            return 'NF' # hotel not found
        
        # generate hotel page url
        detailPageUrl = self.rootUrl['ctrip'] + 'international/' + str(hotelId) + '.html?CheckIn=' + self.checkIn + '&CheckOut=' + self.checkOut + '&Rooms=1'        
        
        # goto hotel detail page with params using GET
        pageDetail, resources = self.ghost.open(detailPageUrl)
        
        # wait for detail_price
        try:
            self.ghost.wait_for_selector('#detail_price dfn')
        except Exception,e:
            print '[ERROR]price cannot be found ... ' + str(detailPageUrl)
            print Exception,":",e  
            return 'NP' # lowest price not found, usually no room available for selected date interval
        
        #  &Price=1683&
        return self.getPriceRegex(self.ghost.content)
                
    def getSearchUrlCtrip(self,detail):
        """
        
        """
        #domestic
        #http://hotels.ctrip.com/Domestic/Tool/AjaxIndexCityNew.aspx?keyword=shanghai
        # getting ctrip's location id from their API
        
        # need to html encode the keyword
        queryKeyword = urllib2.quote(detail['city'])        
        urlApi = self.rootUrl['ctrip'] + 'international/Tool/cityFilter_J.ashx?IsUseNewStyle=T&keyword=' + queryKeyword                
        
        urlData = urllib2.urlopen(urlApi)
        urlDataStr = urlData.read()   
        
        #peek(urlApi,urlDataStr)
        
        a = urlDataStr.split('@')        
        try:
            for b in a:
                b = unicode(b,'utf-8')
            #a[1] = a[1].encode('gbk')        
            del a[0]
            del a[-1]        
            c = a[0].split('|')        

            #locationName = c[4]
            if(c[2] != 'city'):
                locationId = c[5]
            else:
                locationId = c[3]       
        except:
            peek('Location not found',urlApi, urlDataStr)
            return None
        
        #hotelName to search for should be url encoded
        hotelName = urllib2.quote(detail['name_en'])
        
        #return self.rootUrl + 'international/'+str(locationName)+str(locationId)+'/k2'+hotelName
        return self.rootUrl['ctrip'] + 'international/'+str(locationId)+'/k2'+hotelName
    
    def getSearchUrlQunar(self,detail):
        urlApi = 'http://hs.qunar.com/api/hs/citysug?isMainland=true&city='
        queryKeyword = urllib2.quote(detail['city'])  
        apiUrl = urlApi + str(queryKeyword)
        apiData = urllib2.urlopen(apiUrl)
        apiDataStr = apiData.read()   
        apiDataJson = json.loads(apiDataStr)        
        '''
        peek(urlApi,apiDataStr,apiDataJson)
        print type(apiDataJson)        
        print type(apiDataJson['data'])
        print apiDataJson['data'][0]['o']
        '''
        #fromDate=2014-08-02&cityurl=singapore_city&from=hotellist&toDate=2014-08-17
        return self.rootUrl['qunar'] + 'city/' + str(apiDataJson['data'][0]['o']) + '/q-' + str(urllib2.quote(detail['name_en'])) + '#fromDate=' +  str(detail['check_in_date']) + '&toDate=' + str(detail['check_out_date'])
        
    
    def getZanaduDetailUrl(self,detail):
        """
        
        """        
        return self.rootUrl['zanadu'] + 'hotel/'+str(detail['package_id'])  
                    
    def queryCtrip(self,detail):
        """
        
        """
        self.resetGhost()
        
        detail['target_site'] = 'ctrip'
        
        # get the url for searching a hotel
        try:
            urlSearch = self.getSearchUrlCtrip(detail)
        except Exception,e:
            print '[ERROR]hotel cannot be searched ... ' + str(detail)
            print Exception,":",e  
            return detail        
        
        # assign target_url to detail
        detail['target_url'] = urlSearch
                
        if(urlSearch != None):
            self.ghost.open(urlSearch, wait=False)        
            try:
                self.ghost.wait_for_selector('.hotel_list')
            except:
                '''pageContent = self.ghost.content
                fileName = "testwhctripDetails.html"
                fp = open(fileName,'w')
                fp.write(pageContent)
                fp.close()'''            
                #peek(self.ghost.content,urlSearch)
                        
        noResultFlag = self.isNoResult(self.ghost.content)        
                
        if(noResultFlag == None):            
            lowestPrice = self.getLowestPriceCtrip(self.ghost.content)
        else:            
            lowestPrice = 'NF'  # hotel not found
        
        if(lowestPrice == 'NF'):            
            peek('Hotel not found ... ',urlSearch)
                
        detail['lowest_price'] = lowestPrice
                                                
        saveStatus = self.savePrice(detail)
        #if(saveStatus):            
            #log save error
            
        # log the page that price cannot be found
        '''pageContent = self.ghost.content
        fileName = "testwhctripDetails_"+str(hotel['id'])+".html"
        fp = open(fileName,'w')
        fp.write(pageContent)
        fp.close()'''
        
        return detail
    
    def queryZanadu(self,detail):
        """
        
        """
        self.resetGhost()
        detail['target_site'] = 'zanadu'
        
        # get the url for searching a hotel        
        urlSearch = self.getZanaduDetailUrl(detail)
        
        # assign target_url to detail
        detail['target_url'] = urlSearch        
        
        #open(self, address, method='get', headers={}, auth=None, body=None,default_popup_response=None, wait=True)            
        self.ghost.open(urlSearch , wait = False) 
        #self.ghost.wait_for_selector('.right price text-right div')
        self.ghost.wait_for_selector('.controls')
        #self.ghost.wait_for_text('?')
        
        #document.querySelector('strong.small').innerHTML = "";
        PriceSelectorJs = """(function () {                                                
                        var element = document.querySelector('strong').textContent;
                        return element;
                    })();"""
        zPrice, resources = self.ghost.evaluate(PriceSelectorJs);
        
        #peek(urlSearch,zPrice)
        
        zPrice = zPrice.replace(' ','')
        zPrice = zPrice.replace(',','')
        zPrice = zPrice.replace('Â¥','')                                               
        lowestPrice = zPrice                                
                
        detail['lowest_price'] = lowestPrice
                                               
        saveStatus = self.savePrice(detail)
        #if(saveStatus):            
            #log save error
                            
        return detail
    
    def queryQunar(self,detail):
        """
        
        """
        self.resetGhost()
        detail['target_site'] = 'qunar'        
        #http://hs.qunar.com/api/hs/citysug?isMainland=true&city=singapore
        
        searchUrl = self.getSearchUrlQunar(detail)
        detail['target_url'] = searchUrl  
                        
        self.ghost.open(searchUrl,wait=False)
        self.ghost.wait_for_selector('.position_r')
        
        priceSelectorJs = """(function () {
                        var element = document.querySelector('.position_r .c4 span a strong').textContent
                        return element;
                    })();"""
        price = self.ghost.evaluate(priceSelectorJs);
        
        detail['lowest_price'] = price[0]
        
        '''pageContent = self.ghost.content
        fileName = "testwh.html"
        fp = open(fileName,'w')
        fp.write(pageContent)
        fp.close()'''
        
        saveStatus = self.savePrice(detail)
        
        return detail
        
    def queryDetail(self,detail):    
        detail['query_date'] = self.queryDate
        detail['check_in_date'] = self.checkIn
        detail['check_out_date'] = self.checkOut
        detail = self.queryQunar(detail)
        detail = self.queryCtrip(detail)
        detail = self.queryZanadu(detail)
        
        time.sleep(1)
        return detail
    
    def exportToCsv(self):
        csvWhereSql = ' '
        csvSql = 'SELECT p.name_en, crawler_hotel.lowest_price, crawler_hotel.target_site, crawler_hotel.query_date, crawler_hotel.target_url,crawler_hotel.check_in_date, crawler_hotel.check_out_date FROM package as p RIGHT JOIN crawler_hotel ON p.id = crawler_hotel.package_id '+ csvWhereSql ;        
        self.cur.execute(csvSql)
        csvData = []        
        for row in self.cur.fetchall():                
            if(row['lowest_price']=='NP'):
                row['lowest_price'] = 'Price not found in ctrip'
            elif(row['lowest_price']=='NF'):
                row['lowest_price'] = 'Hotel not found in ctrip'
            csvData.append([
                row['name_en'],
                row['target_site'],
                row['lowest_price'],
                row['check_in_date'],
                row['check_out_date'],
                row['query_date'],
                row['target_url']
            ]); 
                
        print 'writing...'
        csvfile = file('csv_test_ctrip.csv', 'wb')       
        writer = csv.writer(csvfile)
        writer.writerow(['Hotel Name Eng', 'Target Site', 'Lowest Price','Check In Date','Check Out Date','Query Date','Target Url'])        
        writer.writerows(csvData)
        csvfile.close()
        #with open('testwh.csv', 'wb') as csvfile:
            #spamwriter = csv.writer(csvfile,dialect='excel')
            #print spamwriter.writerow(['a', '1', '1', '2', '2'])
        return 0
"""
main()
"""
if __name__ == "__main__":       
    
    ### input section ###
    inputParams = parseInput(sys.argv)
    print "inputParams...",inputParams
    validateInputParams(inputParams)      
    
    ### script start ###
    print "zCrawlerStart..."
    
    timeStart = time.time()
    
    ### print ip ###
    #localIP = socket.gethostbyname(socket.gethostname())# get local ip
    #print (localIP)
    ipList = socket.gethostbyname_ex(socket.gethostname())
    #for i in ipList:
    print ipList
        #if i != localIP:
           #print (i,end=',')
    
    #init
    crawler = zCrawler()
    
    ### force export excel without crawling     
    #if (inputParams.get('export')>0):        
        #crawler.exportToCsv()        `````
    #exit(0)    
    
    # set checkin/out dates
    crawler.setDates(inputParams['checkin'], inputParams['checkout'])
                    
    # get list of hotel
    crawler.getHotels()    
                            
    print 'number of hotels to query ... ',len(crawler.hotelList)
            
    countHotel = 0
    # start getting lowest price for each hotel    
    for packageId,detail in crawler.hotelList.items():        
        #crawler.crackCtrip(hotel)
        detail = crawler.queryDetail(detail)
        countHotel = countHotel + 1
        if(countHotel%10==0):
            peek('Hotels queried ... ',countHotel)
                
    print crawler.hotelList
    
    print "Done...TimeElaspsed:",time.time()-timeStart