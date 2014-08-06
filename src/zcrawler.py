#coding:utf-8

__author__="haowu"
__date__ ="$Jul 15, 2014 4:35:27 PM$"

from ghost import Ghost
from datetime import *
import MySQLdb, urllib2, socket, os, sys, time, json, re, csv, gc, datetime
reload(sys)
sys.setdefaultencoding('utf-8')

def dump_garbage():
    """
    show garbage 
    """
        
    # force collection
    print "\nGARBAGE:"
    gc.collect()

    print "\nGARBAGE OBJECTS:"
    for x in gc.garbage:
        s = str(x)
        if len(s) > 80: s = s[:80]
        print type(x),"\n  ", s

def peek(*p):
    """
    for debuging
    """
    for var in p:
        print var, '[TYPE]', type(var)

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
        
class resultPackage:
    def __init__(self):
        self.package_id = 0
        self.name_en = ''
        self.name_cn = ''
        self.query_date = ''
        self.check_in_date = ''
        self.check_out_date = ''
        self.sites = {
            'zanadu':{
                'lowest_price' : '',
                'target_url' : '',
            },
            'ctrip':{
                'lowest_price' : '',
                'target_url' : '',
            },
            'qunar':{
                'lowest_price' : '',
                'target_url' : '',
            },
        }
    
    def toList(self):
        return 0
        
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
        self.timeout = 30
        self.queryDate = str(date.today())
        self.hotelList = {}
        self.ghost = Ghost()
        self.ghost.wait_timeout = self.timeout
        print 'Ghost.wait_timeout...' , self.ghost.wait_timeout
        self.rootUrl = {
            'ctrip' : 'http://hotels.ctrip.com/',
            'qunar' : 'http://hotel.qunar.com/',
            'zanadu' : 'http://www.zanadu.cn/'
        }
        
    def getHotels(self):
        """
        
        """
        #sqlWhere = ' WHERE p.published = 1 AND p.type = 1 AND p.id >= 193 '
        #sqlWhere = ' WHERE p.published = 1 AND p.type = 1 AND p.id IN (17) '
        sqlWhere = ' WHERE p.published = 1 AND p.type = 1 '        
        
        #sqlWhere = ' WHERE p.published = 1 AND p.type = 1 AND p.id IN (36,461,20,403,40,18) '        
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
      
    def logPage(self):
        pageContent = self.ghost.content
        fileName = "pagelog.html"
        fp = open(fileName,'w')
        fp.write(pageContent)
        fp.close()     
        
    def resetGhost(self):
        #self.ghost.exit()
        del self.ghost 
        self.ghost = Ghost()
        self.ghost.wait_timeout = self.timeout
        
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
            if(k in ['package_id','name_en','name_cn','target_url','target_site','lowest_price','query_date','check_in_date','check_out_date']):                
                setSql = setSql + '`' + str(k) + '`' + '=' + '"' + str(v) + '"' + ', '
            
            if (k in ['lowest_price','target_url'])  :
                setUpdateSql = setUpdateSql + '`' + str(k) + '`' + '=' + '"' + str(v) + '"' + ', '
            elif (k in ['package_id','target_site','query_date','check_in_date','check_out_date']) :
                whereSql = whereSql + '`' + str(k) + '`' + '=' + '"' + str(v) + '"' + ' AND '
        whereSql = whereSql.rstrip('AND ')
        insertSql = insertSql + setSql + '`creation_time`=NOW(), `last_update_time`=NOW() '
        updateSql = updateSql + setUpdateSql + '`last_update_time`=NOW() ' + whereSql
        
        #peek(insertSql,updateSql)                
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
        domestic = 0
        hotelIdContainer = 'hotel_list_item'
        if(detail['country'] in ['china','China']):
            domestic = 1
            hotelIdContainer = 'searchresult_list'
        hotelIdSelectorJs = """(function () {
                        var element = document.querySelector('."""+hotelIdContainer+"""').id
                        return element;
                    })();"""
        hotelId, resources = self.ghost.evaluate(hotelIdSelectorJs);
        
        if(hotelId == None):            
            return 'NF' # hotel not found
        
        # generate hotel page url
        if (domestic==0):
            detailPageUrl = self.rootUrl['ctrip'] + 'international/' + str(hotelId) + '.html?CheckIn=' + self.checkIn + '&CheckOut=' + self.checkOut + '&Rooms=1'        
        else:
            detailPageUrl = self.rootUrl['ctrip'] + 'hotel/' + str(hotelId) + '.html?CheckIn=' + self.checkIn + '&CheckOut=' + self.checkOut + '&Rooms=1'        
        # goto hotel detail page with params using GET
        self.ghost.open(detailPageUrl, wait=False)
        
        # wait for detail_price
        try:
            priceContainer = '#detail_price dfn'
            if (domestic == 1):
                #priceContainer = '#HideIsNoneLogin'
                #priceContainer = '&Price='
                priceContainer = 'hotel.detail'
                self.ghost.wait_for_text(priceContainer)
            else:
                self.ghost.wait_for_selector(priceContainer)
            
        except Exception,e:
            print '[ERROR]price cannot be found ... ' + str(detailPageUrl)
            print Exception,":",e                                      
            #self.logPage()
            return 'NP' # lowest price not found, usually no room available for selected date interval
        
        #  &Price=1683&     
        
        #self.logPage()
        
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
           
    def getLocationIdCtripIntl(self,locatoinData):
        a = locatoinData.split('@')                
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
        return locationId
    
    def getLocationIdCtripDomestic(self,locatoinData):        
        a = locatoinData.split('@')             
        #for b in a:
            #b = unicode(b,'utf-8')
        #a[1] = a[1].encode('gbk')   
        
        del a[0]
        del a[-1]      
        
        c = a[0].split('|')        
        
        #if(c[2] != 'city'):
            #locationId = c[5]
        #else:
            #locationId = c[3]   
        return (str(c[0]) + str(c[2]))
    
    def getSearchUrlCtrip(self,detail):
        """
        
        """
        #domestic
        #http://hotels.ctrip.com/Domestic/Tool/AjaxIndexCityNew.aspx?keyword=shanghai
        # getting ctrip's location id from their API
        domestic = 0
        if(detail['country'] in ['china','China']):
            domestic = 1
        
        
        # need to html encode the keyword
        if(detail['city'] == 'Kamala'):
            detail['city'] = 'Kamala Sea View'
        detail['city'] = detail['city'].replace('-','')
        queryKeyword = urllib2.quote(detail['city'])                
        urlApi = self.rootUrl['ctrip'] + 'international/Tool/cityFilter_J.ashx?IsUseNewStyle=T&keyword=' + queryKeyword   
        if (domestic==1):
            urlApi = self.rootUrl['ctrip'] + 'Domestic/Tool/AjaxIndexCityNew.aspx?keyword=' + queryKeyword   
                        
        urlData = urllib2.urlopen(urlApi)
        urlDataStr = urlData.read()   
        
        #peek(urlDataStr)        
        
        #try:
        if(domestic == 0):
            locationId = self.getLocationIdCtripIntl(urlDataStr)
        else:
            locationId = self.getLocationIdCtripDomestic(urlDataStr)
        #except:
            #peek('Location not found',urlApi, urlDataStr)
            #return None
            
        #hotelName to search for should be url encoded
        #hotelName = urllib2.quote(detail['name_en'])
        hotelName = str(detail['name_en'])
        
        if(domestic == 0):                 
            return self.rootUrl['ctrip'] + 'international/'+str(locationId)+'/k2'+hotelName + '?checkin=' +self.checkIn+'&checkout='+self.checkOut
        else:
            return self.rootUrl['ctrip'] + 'hotel/'+str(locationId)+'/k1'+hotelName + '?checkin=' +self.checkIn+'&checkout='+self.checkOut
    
    def getSearchUrlQunar(self,detail):
        if(detail['city']=='Bali'):
            detail['city']='Balidao'
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
        '''
        #print apiDataJson
        
        #fromDate=2014-08-02&cityurl=singapore_city&from=hotellist&toDate=2014-08-17
        try:
            cityPath = str(apiDataJson['data'][0]['o'])
        except:
            peek(apiUrl)
            return None
        #hotelName = str(urllib2.quote(detail['name_en']))
        hotelName = str(detail['name_en'])
        return self.rootUrl['qunar'] + 'city/' + cityPath + '/q-' + hotelName + '#fromDate=' +  str(detail['check_in_date']) + '&toDate=' + str(detail['check_out_date'])
        
    
    def getZanaduDetailUrl(self,detail):
        """
        
        """        
        #return self.rootUrl['zanadu'] + 'hotel/'+str(detail['package_id'])  
        return self.rootUrl['zanadu'] + 'hotel/selectRooms?package_id='+str(detail['package_id'])+'&check_in='+str(detail['check_in_date'])+'&check_out='+str(detail['check_out_date'])
                    
    def queryCtrip(self,detail):
        """
        
        """
        #self.resetGhost()
        
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
            #self.logPage()
            peek('Hotel not found ... ',urlSearch)
        else:            
            countNights = datetime.datetime.strptime(self.checkOut,'%Y-%m-%d') - datetime.datetime.strptime(self.checkIn,'%Y-%m-%d')
            #peek('nights',countNights.days)
            detail['lowest_price'] = int(lowestPrice) * int(countNights.days)
        
                                                
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
        #self.resetGhost()
        detail['target_site'] = 'zanadu'
        
        # get the url for searching a hotel        
        urlSearch = self.getZanaduDetailUrl(detail)
        
        # assign target_url to detail
        detail['target_url'] = urlSearch   
        
        #open(self, address, method='get', headers={}, auth=None, body=None,default_popup_response=None, wait=True)            
        self.ghost.open(urlSearch , wait = False) 
        #self.ghost.wait_for_selector('.right price text-right div')
        #self.ghost.wait_for_selector('.controls')
        #self.ghost.wait_for_selector('.col-right.price-night.room-price')
        try:
            self.ghost.wait_for_selector('.amount')        
            PriceSelectorJs = """(function () {                                                
                        var element = document.querySelector('.amount').textContent;
                        return element;
                    })();"""
            zPrice, resources = self.ghost.evaluate(PriceSelectorJs);

            #peek(urlSearch,zPrice)

            zPrice = zPrice.replace(' ','')
            zPrice = zPrice.replace(',','')
            #zPrice = zPrice.replace('Â¥','')                                               
            lowestPrice = zPrice                                

            detail['lowest_price'] = lowestPrice
        except:
        #self.ghost.wait_for_text('?')
        #self.logPage()
        #document.querySelector('strong.small').innerHTML = "";
            detail['lowest_price'] = 'NP'
                                               
        saveStatus = self.savePrice(detail)
        #if(saveStatus):            
            #log save error
                            
        return detail
    
    def queryQunar(self,detail):
        """
        
        """
        #self.resetGhost()
        detail['target_site'] = 'qunar'        
        #http://hs.qunar.com/api/hs/citysug?isMainland=true&city=singapore
        
        try:
            searchUrl = self.getSearchUrlQunar(detail)
        except:
            searchUrl = None
        detail['target_url'] = searchUrl  
                        
        self.ghost.open(searchUrl,wait=False)
        try:
            self.ghost.wait_for_selector('#js-singleHotel div .position_r') 
            #self.ghost.wait_for_selector('.position_r') 
            
            priceSelectorJs = """(function () {
                    var element = document.querySelector('#js-singleHotel div .position_r .c4 span a strong').textContent
                    return element;
                })();"""
            price = self.ghost.evaluate(priceSelectorJs);  
            
            if(price[0] != None):
                detail['lowest_price'] = price[0]
            else:
                peek(searchUrl)
                detail['lowest_price'] = 'NP'
         
            self.logPage()
            '''priceSelectorJs = """(function () {
                    var element = document.querySelector('.position_r .c4 span a strong').textContent
                    return element;
                })();"""
            price = self.ghost.evaluate(priceSelectorJs);'''
            #self.ghost.wait_for_selector('.position_r')
            #self.ghost.wait_for_selector('.namered')  
        except:
            peek('Hotel not found',searchUrl)          
            detail['lowest_price'] = 'NF'
            '''
            pageContent = self.ghost.content
            fileName = "testwh.html"
            fp = open(fileName,'w')
            fp.write(pageContent)
            fp.close()
            peek(detail)
            exit(0)'''                                
        
        #self.logPage()
        saveStatus = self.savePrice(detail)
        
        return detail
        
    def queryDetail(self,detail):    
        detail['query_date'] = self.queryDate
        detail['check_in_date'] = self.checkIn
        detail['check_out_date'] = self.checkOut
        detail = self.queryQunar(detail)
        detail = self.queryCtrip(detail)
        detail = self.queryZanadu(detail)
        
        #time.sleep(1)
        return detail
    
    def exportToCsv(self):
        fileName = 'priceParity'+str(self.queryDate)+'.csv'
        csvWhereSql = ' WHERE `query_date` = "' + str(self.queryDate) + '" AND `check_in_date`="'+ str(self.checkIn) + '" AND `check_out_date`="' + str(self.checkOut) + '"'
        csvSql = 'SELECT crawler_hotel.package_id, p.name_en, crawler_hotel.lowest_price, crawler_hotel.target_site, crawler_hotel.target_url, crawler_hotel.query_date, crawler_hotel.check_in_date, crawler_hotel.check_out_date FROM package as p RIGHT JOIN crawler_hotel ON p.id = crawler_hotel.package_id '+ csvWhereSql ;                
        self.cur.execute(csvSql)
        csvData = {}
        #csvData.append(['Hotel Name Eng', 'Target Site', 'Lowest Price','Check In Date','Check Out Date','Query Date','Target Url'])
        csvData[0] = {
            'HotelName': 'HotelName',
            'CheckInDate' : 'CheckInDate',
            'CheckOutDate' : 'CheckOutDate',
            'QueryDate' : 'QueryDate',
            'TargetSiteZanadu' : 'TargetSite',
            'LowestPriceZanadu' : 'LowestPriceZanadu',
            'TargetUrlZanadu' : 'TargetUrlZanadu',
            'TargetSiteCtrip' : 'TargetSite',
            'LowestPriceCtrip' : 'LowestPriceCtrip',
            'TargetUrlCtrip' : 'TargetUrlCtrip',
            'TargetSiteQunar' : 'TargetSite',
            'LowestPriceQunar' : 'LowestPriceQunar',
            'TargetUrlQunar' : 'TargetUrlQunar',            
        }
        for row in self.cur.fetchall():   
            #peek(row,csvData)            
            if(csvData.get(str(row['package_id'])) == None):
                csvData[str(row['package_id'])] = {
                    'HotelName': '',
                    'CheckInDate' : '',
                    'CheckOutDate' : '',
                    'QueryDate' : '',
                    'TargetSiteZanadu' : '',
                    'LowestPriceZanadu' : '',
                    'TargetUrlZanadu' : '',
                    'TargetSiteCtrip' : '',
                    'LowestPriceCtrip' : '',
                    'TargetUrlCtrip' : '',
                    'TargetSiteQunar' : '',
                    'LowestPriceQunar' : '',
                    'TargetUrlQunar' : '',   
                }
                
            csvData[str(row['package_id'])]['HotelName'] = row['name_en']
            csvData[str(row['package_id'])]['CheckInDate'] = str(row['check_in_date'])
            csvData[str(row['package_id'])]['CheckOutDate'] = str(row['check_out_date'])
            csvData[str(row['package_id'])]['QueryDate'] = str(row['query_date'])
            '''if(row['lowest_price']=='NP'):
                row['lowest_price'] = 'Price NotFound'
            elif(row['lowest_price']=='NF'):
                row['lowest_price'] = 'Hotel NotFound' '''           
            if(row['target_site'] == 'zanadu'):
                csvData[str(row['package_id'])]['TargetSiteZanadu'] = row['target_site']
                csvData[str(row['package_id'])]['LowestPriceZanadu'] = row['lowest_price']
                csvData[str(row['package_id'])]['TargetUrlZanadu'] = row['target_url']
            elif(row['target_site'] == 'ctrip'):
                csvData[str(row['package_id'])]['TargetSiteCtrip'] = row['target_site']
                csvData[str(row['package_id'])]['LowestPriceCtrip'] = row['lowest_price']
                csvData[str(row['package_id'])]['TargetUrlCtrip'] = row['target_url']
            elif(row['target_site'] == 'qunar'):
                csvData[str(row['package_id'])]['TargetSiteQunar'] = row['target_site']
                csvData[str(row['package_id'])]['LowestPriceQunar'] = row['lowest_price']
                csvData[str(row['package_id'])]['TargetUrlQunar'] = row['target_url']
            
            '''
            csvData.append([
                row['name_en'],                
                row['target_site'],
                row['lowest_price'],
                row['check_in_date'],
                row['check_out_date'],
                row['query_date'],
                row['target_url']
            ]); '''
        #peek(csvData.values())
        
        peek('writing to file ...',fileName )
        csvfile = file(fileName, 'wb')       
        writer = csv.writer(csvfile)             
        for row in csvData.values() :
            #peek(row)
            writer.writerow([
                row['HotelName'],
                row['CheckInDate'],
                row['CheckOutDate'],
                row['QueryDate'],
                row['TargetSiteZanadu'],
                row['LowestPriceZanadu'],
                row['TargetUrlZanadu'],
                row['TargetSiteCtrip'],
                row['LowestPriceCtrip'],
                row['TargetUrlCtrip'],
                row['TargetSiteQunar'],
                row['LowestPriceQunar'],
                row['TargetUrlQunar'],          
            ])
            #writer.writerows(csvData)
            #exit(0)        
        csvfile.close()
        peek('Writting complete...')
        exit(0)
"""
main()
"""
if __name__ == "__main__":     
    
    #gc.enable()
    #gc.set_debug(gc.DEBUG_LEAK)
    
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
        
    # set checkin/out dates
    crawler.setDates(inputParams['checkin'], inputParams['checkout'])
    
    ### force export excel without crawling      
    if (inputParams.get('export') > 0 ):        
        crawler.exportToCsv()                        
                    
    # get list of hotel
    crawler.getHotels()    
                            
    print 'number of hotels to query ... ',len(crawler.hotelList)
            
    countHotel = 0
    # start getting lowest price for each hotel    
    for packageId,detail in crawler.hotelList.items():        
        
        #dump_garbage()
        
        #crawler.crackCtrip(hotel)
        detail = crawler.queryDetail(detail)
        countHotel = countHotel + 1
        if(countHotel%10==0):
            peek('Hotels queried ... ',countHotel)
                        
    print "Done...TimeElaspsed:",time.time()-timeStart
    crawler.exportToCsv()