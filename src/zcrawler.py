# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__="haowu"
__date__ ="$Jul 15, 2014 4:35:27 PM$"

import time

class zCrawler:    
    """
    main class for the crawler
    """
    def __init__(self):        
        self.hotelList = []
    def getHotels(self):
        self.hotelList[0:0] = [1];
        self.hotelList[0:0] = [2];
        return 0

if __name__ == "__main__":    
    print "Hello World"
    timeStart = time.time()
    
    crawler = zCrawler()    
    crawler.getHotels()
        
    print crawler.hotelList
    
    time.sleep(1)
    print "Done...TimeElaspsed:",time.time()-timeStart


