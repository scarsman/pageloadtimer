#!/usr/bin/env python
#
# Copyright (c) 2015 Corey Goldberg
# License: MIT


import collections
import textwrap

from selenium import webdriver
from xvfbwrapper import Xvfb


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
    with Xvfb() as xvfb:
        url = 'http://google.com'
        driver = webdriver.Firefox()
        #driver = webdriver.Chrome()
        #driver = webdriver.PhantomJS()
        driver.get(url)
        timer = PageLoadTimer(driver)
        events_time = timer.get_event_times()
        
        total_page_load_time = ""
        total_request_respond_time = ""
	total_page_render_time = ""
	
	print "** Events Time"
	print "----------------------------"
	for key in events_time.iterkeys():

		print "%s: %s" % (key, events_time[key])

		total_page_load_time = (events_time["loadEventEnd"] - events_time["navigationStart"])
		total_request_respond_time = (events_time["responseEnd"] - events_time["requestStart"])
		total_page_render_time = (events_time["domComplete"] - events_time["domLoading"])

	print "-----------------------------"
		
	print "Total Page Load Time: %s ms" % total_page_load_time 
	print "Total Request Respond Time: %s ms" % total_request_respond_time
	print "Total Page Render Time: %s ms" % total_page_render_time

	
