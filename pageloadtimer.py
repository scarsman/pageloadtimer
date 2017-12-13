#!/usr/bin/env python
#
# Copyright (c) 2015 Corey Goldberg
# License: MIT


import collections
import textwrap

from selenium import webdriver

class PageLoadTimer:

    def __init__(self, driver):
        """
            takes:
                'driver': webdriver instance from selenium.
        """
        self.driver = driver

        self.jscript = textwrap.dedent("""
            var performance = window.performance || {};
            var timings = performance.timing || {};
            return timings;
            """)

    def inject_timing_js(self):
        timings = self.driver.execute_script(self.jscript)
        return timings

    def get_event_times(self):

        timings = self.inject_timing_js()
        # the W3C Navigation Timing spec guarantees a monotonic clock:
        #  "The difference between any two chronologically recorded timing
        #   attributes must never be negative. For all navigations, including
        #   subdocument navigations, the user agent must record the system
        #   clock at the beginning of the root document navigation and define
        #   subsequent timing attributes in terms of a monotonic clock
        #   measuring time elapsed from the beginning of the navigation."
        # However, some navigation events produce a value of 0 when unable to
        # retrieve a timestamp.  We filter those out here:
        good_values = [epoch for epoch in timings.values() if epoch != 0]
        # rather than time since epoch, we care about elapsed time since first
        # sample was reported until event time.  Since the dict we received was
        # inherently unordered, we order things here, according to W3C spec
        # fields.
        ordered_events = ('navigationStart', 'fetchStart', 'domainLookupStart',
                          'domainLookupEnd', 'connectStart', 'connectEnd',
                          'secureConnectionStart', 'requestStart',
                          'responseStart', 'responseEnd', 'domLoading',
                          'domInteractive', 'domContentLoadedEventStart',
                          'domContentLoadedEventEnd', 'domComplete',
                          'loadEventStart', 'loadEventEnd'
                          )
        event_times = ((event, timings[event] - min(good_values)) for event
                       in ordered_events if event in timings)

        return collections.OrderedDict(event_times)


if __name__ == '__main__':

    url = 'http://buzz4pun.com'
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('incognito')
    options.add_argument('window-size=1920x1080')
    driver = webdriver.Chrome(executable_path="/usr/lib/chromium-browser/chromedriver",chrome_options=options)
    driver.implicitly_wait(10)
    
    driver.get(url)

    timer = PageLoadTimer(driver)
    events_time = timer.get_event_times()
   
    driver.quit()
	 
    latency = ""
    transfer = ""
    dom_processing = ""
    dom_interactive = ""
    onload = ""
    total = ""

    print "** Events Time"
    print "----------------------------\n"
    for key in events_time.iterkeys():

    	print "%s: %s" % (key, events_time[key])

        #based on tripadvisor
        #http://engineering.tripadvisor.com/html5-navigation-timing/

        latency = events_time["responseStart"] - events_time["fetchStart"]
        transfer = events_time["responseEnd"] - events_time["responseStart"]
        dom_processing = events_time["domInteractive"] - events_time["domLoading"]
        dom_interactive = events_time["domComplete"] - events_time["domInteractive"]
        onload = events_time["loadEventEnd"] - events_time["loadEventStart"]

    total = latency + transfer + dom_processing + dom_interactive + onload


    print "-----------------------------\n"
    	
    print "total page load: %sms\nlatency: %sms\ntransfer: %sms\ndom processing load to interactive: %sms\ndom processing interactive to complete: %sms\nonload: %sms" % (total, latency, transfer, dom_processing, dom_interactive, onload)

	
