from django.test import TestCase
from oembed.core import replace

class OEmbedTests(TestCase):
    noembed = ur"This is text that should not match any regex."
    end = ur"There is this great video at %s"
    start = ur"%s is a video that I like."
    middle = ur"There is a movie here: %s and I really like it."
    trailing_comma = ur"This is great %s, but it might not work."
    trailing_period = ur"I like this video, located at %s."
    
    locs = [u"http://www.viddler.com/explore/SYSTM/videos/49/",
            u"http://www.slideshare.net/hues/easter-plants",
            u"http://www.scribd.com/doc/28452730/Easter-Cards",
            u"http://screenr.com/gzS",
            u"http://www.5min.com/Video/How-to-Decorate-Easter-Eggs-with-Decoupage-142076462",
            u"http://www.howcast.com/videos/328008-How-To-Marble-Easter-Eggs",
            u"http://my.opera.com/nirvanka/albums/showpic.dml?album=519866&picture=7173711",
            u"http://img20.yfrog.com/i/dy6.jpg/",
            u"http://tweetphoto.com/8069529",
            u"http://www.flickr.com/photos/jaimewalsh/4489497178/",
            u"http://twitpic.com/1cm8us",
            u"http://imgur.com/6pLoN",
            u"http://twitgoo.com/1p94",
            u"http://www.23hq.com/Greetingdesignstudio/photo/5464607",
            u"http://www.youtube.com/watch?v=Zk7dDekYej0",
            u"http://www.veoh.com/browse/videos/category/educational/watch/v7054535EZGFJqyX",
            u"http://www.justin.tv/venom24",
            u"http://qik.com/video/1445889",
            u"http://revision3.com/diggnation/2005-10-06",
            u"http://www.dailymotion.com/video/xcss6b_big-cat-easter_animals",
            u"http://www.collegehumor.com/video:1682246",
            u"http://www.twitvid.com/BC0BA",
            u"http://www.break.com/usercontent/2006/11/18/the-evil-easter-bunny-184789",
            u"http://vids.myspace.com/index.cfm?fuseaction=vids.individual&videoid=103920940",
            u"http://www.metacafe.com/watch/2372088/easter_eggs/",
            u"http://blip.tv/file/770127",
            u"http://video.google.com/videoplay?docid=2320995867449957036",
            u"http://www.revver.com/video/1574939/easter-bunny-house/",
            u"http://video.yahoo.com/watch/4530253/12135472",
            u"http://www.viddler.com/explore/cheezburger/videos/379/",
            u"http://www.liveleak.com/view?i=d91_1239548947",
            u"http://www.hulu.com/watch/23349/nova-secrets-of-lost-empires-ii-easter-island",
            u"http://movieclips.com/watch/jaws_1975/youre_gonna_need_a_bigger_boat/",
            u"http://crackle.com/c/How_To/How_to_Make_Ukraine_Easter_Eggs/2262274",
            u"http://www.fancast.com/tv/Saturday-Night-Live/10009/1083396482/Easter-Album/videos",
            u"http://www.funnyordie.com/videos/040dac4eff/easter-eggs",
            u"http://vimeo.com/10429123",
            u"http://www.ted.com/talks/robert_ballard_on_exploring_the_oceans.html",
            u"http://www.thedailyshow.com/watch/tue-february-29-2000/headlines---leap-impact",
            u"http://www.colbertnation.com/the-colbert-report-videos/181772/march-28-2006/intro---3-28-06",
            u"http://www.traileraddict.com/trailer/easter-parade/trailer",
            u"http://www.lala.com/#album/432627041169206995/Rihanna/Rated_R",
            u"http://www.amazon.com/gp/product/B001EJMS6K/ref=s9_simh_gw_p200_i1?pf_rd_m=ATVPDKIKX0DER",
            u"http://animoto.com/s/oH9VwgjOU9hpbgYXNDwLNQ",
            u"http://xkcd.com/726/"]

    
    def get_oembed(self, url):
        try:
            return replace('%s' % url)
        except Exception, e:
            self.fail("URL: %s failed for this reason: %s" % (url, str(e)))
    
    def testNoEmbed(self):
        self.assertEquals(
            replace(self.noembed),
            self.noembed
        )
    
    def testEnd(self):
        for loc in self.locs:
            embed =  self.get_oembed(loc) 
            
            if not embed or embed == loc:
                self.fail("URL: %s did not produce an embed object" % loc)
            
            for text in (self.end, self.start, self.middle, self.trailing_comma, self.trailing_period):
                self.assertEquals(
                    replace(text % loc),
                    text % embed
                )

    
    def testManySameEmbeds(self):
        loc = self.locs[1]
        embed =  self.get_oembed(loc)
        
        text = " ".join([self.middle % loc] * 100) 
        resp = " ".join([self.middle % embed] * 100)
        self.assertEquals(replace(text), resp)