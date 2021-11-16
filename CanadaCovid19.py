# CanadaCovid class definition
# Dr. Bogdan Hlevca, Markham, Ontario, Canada
# April 2020
#
# Adapted after Dr. Tirthajyoti Sarkar, Fremont, CA, https://github.com/tirthajyoti/Covid-19-analysis

import numpy as np
import pandas as pd
import io
import sys
import requests
import matplotlib.pyplot as plt
import time
from datetime import date, datetime, timedelta
import math


# --------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------
class CanadaCovid19(object):
    """
    Class to analyze the Covid-19 Canadian data from:
        https://health-infobase.canada.ca/src/data/covidLive/covid19.csv
    """

    def __init__(self):
        """
        PEP8 initialize here
        """
        self.provincedict = {}
        self.countrydict = {}
        self.provincelist = None
        self.countrydf = None
        self._updated = False
        self._processed = False

        self._today = date.today()
        self.provinceList = ['Ontario', 'Quebec', 'British Columbia',
                             'Manitoba', 'Saskatchewan', 'Alberta', 'Prince Edward Island',
                             'New Brunswick', 'Newfoundland and Labrador', 'Nova Scotia',
                             'Yukon', 'Northwest Territories', 'Nunavut']

    # --------------------------------------------------------------------------------------------------------------
    def runScenarioOne(self, country):
        country = country
        self.updateCountry()
        self.dateUpdate()
        self.process(country)
        #the data of
        start500 = datetime.fromisoformat('2020-03-18')
        self.plotMultiProvince(self.provinceList, last_30_days=False, date_500cases=start500)
        print("")
        self.rankProvince(N=5, daterank=None)
        print("")
        if False:
            self.scenarioPrediction(rateWINDOW=5, time_int=30)
            print("")
        self.plotProvince(country, iscountry=True)
        print("")
        # province sort
        res = self.sortProvinces(N=5)
        [dt, sorted_cases, sorted_deaths, sorted_newcases, sorted_newdeaths] = res
        for p in self.provinceList:
            if p != country:
                self.plotProvince(p)
                print("")


    # --------------------------------------------------------------------------------------------------------------
    def today(self):
        """Print today's date"""
        print("Today is:", self._today)

    # --------------------------------------------------------------------------------------------------------------
    def updateCountry(self,
                      url="https://health-infobase.canada.ca/src/data/covidLive/covid19.csv"):
        """
        OLD HEADER: pruid,prname,prnameFR,date,numconf,numprob,numdeaths,numtotal,numtoday,percentoday,numtested
        ----------------------------------------------------------------------------------------------------------------------------------------
                   A    B       C       D     E       F       G         H         I          J          K              L        M         N
        ----------------------------------------------------------------------------------------------------------------------------------------
        HEADER: pruid,prname,prnameFR,date,numconf,numprob,numdeaths,numtotal,numtested,numrecover,percentrecover,ratetested,numtoday,percentoday
        HEADER: pruid	prname	prnameFR	date	update	numconf	numprob	numdeaths	numtotal	numtested	numtests	numrecover	percentrecover	ratetested	ratetests	numtoday	percentoday	ratetotal	ratedeaths	numdeathstoday	percentdeath	numtestedtoday	numteststoday	numrecoveredtoday	percentactive	numactive	rateactive	numtotal_last14	ratetotal_last14	numdeaths_last14	ratedeaths_last14	numtotal_last7	ratetotal_last7	numdeaths_last7	ratedeaths_last7	avgtotal_last7	avgincidence_last7	avgdeaths_last7	avgratedeaths_last7

        :param url:
        :return:
        """
        url = url
        s = requests.get(url).content
        self.countrydf = pd.read_csv(io.StringIO(s.decode('utf-8')))
        self.countrydf['date'] = pd.to_datetime(self.countrydf['date'], format='%d-%m-%Y')
        self.countryName = None
        self._updated = True

    # --------------------------------------------------------------------------------------------------------------
    def dateUpdate(self):
        """
        update the data
        :return:
        """
        if self._updated:
            print("Date of the latest data:", self.countrydf.iloc[-1]['date'].date())
            now = datetime.now()
            print("Time of latest pull:", now.strftime("%H:%M:%S"))
        else:
            self._today = date.today()
            print("Data was not updated, updating now: {}".format(self._today))

    # --------------------------------------------------------------------------------------------------------------
    def peek(self):
        """
        Print the first 5 rows
        :return:
        """
        if self._updated:
            print("First 5 rows of the Country data")
            print("=" * 50)
            print(self.countrydf.head())
            print("*************************************************")
            print("First 5 rows of the Province data")
            print("=" * 50)
            print(self.provincedf.head())

    # --------------------------------------------------------------------------------------------------------------
    def process(self, country):
        """
        Proscess the the loaded data if uptodate
        :param country:
        :return:
        """

        def calculateNewcasesDeathsAndTested(dataframe):
            """
            determine deaths based on today and previous day total deaths
            :param dataframe:
            :return:
            """

            tdc = []
            tc = []
            tt = []
            tts = []
            i = 0
            secondswitch = False
            prevc = prevd = 0
            for c, d, t, ts in zip(dataframe['totalcases'], dataframe['totaldeaths'],
                                   dataframe['numtested'], dataframe['numtests']):
                #data bug and I have no way of contacting the morons
                if ts == '1,345,309':
                    ts = '0'
                if isinstance(ts, str):
                    ts=int(ts)
                if i != 0:
                    tdc.append(d - prevd)
                    tc.append(c - prevc)
                    if not math.isnan(t):
                        tt.append(t - prevt)
                        secondswitch = True
                    else:
                        if secondswitch:
                            tt.append(1000)
                            secondswitch = False
                        else:
                            tt.append(ts - prevt)
                else:
                    tdc.append(d)
                    tc.append(c)
                    if not math.isnan(t):
                        tt.append(t)
                    else:
                        tt.append(0)
                prevd = d
                prevc = c
                if not math.isnan(t):
                    prevt = t
                else:
                    prevt = int(ts)
                i += 1
            ds_newdeaths = pd.Series(tdc, index=dataframe.index)
            ds_newcases = pd.Series(tc, index=dataframe.index)
            ds_newtested = pd.Series(tt, index=dataframe.index)
            dataframe['newdeaths'] = ds_newdeaths
            dataframe['newcases'] = ds_newcases
            dataframe['newtested'] = ds_newtested
            return dataframe

        pd.set_option('mode.chained_assignment', None)
        self.countryName = country
        print("Processing...")
        t1 = time.time()
        if self._updated:
            country_df = self.countrydf[self.countrydf['prname'] == country]
            country_df['newcases'] = country_df['numtoday']
            country_df['totaldeaths'] = country_df['numdeaths']
            country_df['totalcases'] = country_df['numtotal']
            country_df['prcnewcases'] = country_df['percentoday']
            country_df['confcases'] = country_df['numconf']
            country_df['probcases'] = country_df['numprob']
            country_df['numtested'] = country_df['numtested']
            country_df['numtests'] = country_df['numtests']
            country_df['numrecover'] = country_df['numrecover']
            country_df['prcrecover'] = country_df['percentrecover']
            country_df['ratetested'] = country_df['ratetested']
            country_df = calculateNewcasesDeathsAndTested(country_df)
            self.countrydict[country] = country_df

            # provinces
            self.provincelist = list(self.countrydf['prname'].unique())
            for c in self.provincelist:
                if c != country:
                    province_df = self.countrydf[self.countrydf['prname'] == c]
                    province_df['totaldeaths'] = province_df['numdeaths']
                    province_df['totalcases'] = province_df['numtotal']
                    province_df['prcnewcases'] = province_df['percentoday']
                    province_df['confcases'] = province_df['numconf']
                    province_df['probcases'] = province_df['numprob']
                    province_df['numtested'] = province_df['numtested']
                    province_df['numtests'] = province_df['numtests']
                    province_df['numrecover'] = province_df['numrecover']
                    province_df['prcrecover'] = province_df['percentrecover']
                    province_df['ratetested'] = province_df['ratetested']

                    province_df = calculateNewcasesDeathsAndTested(province_df)
                    self.provincedict[c] = province_df
                    # new cases seems not to be maintained anymore so we calculate them from totalcases
                    # province_df['newcases'] = province_df['numtoday']
                    # if pd.isna(province_df['newcases'].iloc[-1]):
                    #   province_df['totaldeaths'] = country_df['numdeaths']

        self._processed = True
        t2 = time.time()
        delt = round(t2 - t1, 3)
        print("Finished. Took {} seconds".format(delt))


    # --------------------------------------------------------------------------------------------------------------
    def plotProvince(self,
                     province='Ontario',
                     iscountry=False,
                     last_30_days=False,
                     show_tested=False):
        """
        Plots countrywise data and province data: total and new cases and deaths
        """
        if not self._processed:
            print("Data not processed yet. Cannot plot countrywise.")
            return None

        s = str(province)
        assert s in self.provincelist, "Input does not appear in the list of provinces. Possibly wrong name/spelling"
        if iscountry:
            df = self.countrydict[s]
        else:
            df = self.provincedict[s]

        dates = df['date']
        cases = df['totalcases']
        deaths = df['totaldeaths']
        newcases = df['newcases']
        newdeaths = df['newdeaths']
        newtested = df['newtested']
        numtests = df['numtests']
        numrecover = df['numrecover']

        if last_30_days:
            dates = df['date'][-31:-1]
            cases = df['totalcases'][-31:-1]
            deaths = df['totaldeaths'][-31:-1]
            newcases = df['newcases'][-31:-1]
            newdeaths = df['newdeaths'][-31:-1]
            numtested = df['numtested'][-31:-1]
            numtests = df['numtests'][-31:-1]
            numrecover = df['numrecover'][-31:-1]

        # if pd.isna(newcases).any():
        #    newcases.values[:] = 0

        plt.figure(figsize=(13, 7))
        if last_30_days:
            plt.title("Cumulative cases in {}, for last 30 days".format(s), fontsize=18)
        else:
            plt.title("Cumulative cases in {}".format(s), fontsize=18)

        plt.bar(dates.values, cases, color='blue', edgecolor='blue')
        plt.xticks(rotation=45, fontsize=14)
        plt.subplots_adjust(bottom=0.22)
        plt.grid()
        plt.show()


        print()

        plt.figure(figsize=(13, 7))
        if last_30_days:
            plt.title("Cumulative deaths in {}, for last 30 days".format(s), fontsize=18)
        else:
            plt.title("Cumulative deaths in {}".format(s), fontsize=18)
        plt.bar(dates.values, deaths, color='red', edgecolor='red')
        plt.xticks(rotation=45, fontsize=14)
        plt.subplots_adjust(bottom=0.22)
        plt.grid()
        plt.show()
        print()

        plt.figure(figsize=(13, 7))
        if last_30_days:
            plt.title("New cases in {}, for last 30 days".format(s), fontsize=18)
        else:
            plt.title("New cases in {}".format(s), fontsize=18)

        plt.bar(dates.values, newcases, color='yellow', edgecolor='yellow')
        plt.xticks(rotation=45, fontsize=14)
        plt.subplots_adjust(bottom=0.22)
        plt.grid()
        plt.show()
        print()

        plt.figure(figsize=(13, 7))
        wd = np.timedelta64(24,'h')
        w = np.timedelta64(8, 'h')



        if last_30_days:
            plt.title("New cases vs. Tested in {}, for last 30 days".format(s), fontsize=18)
        else:
            plt.title("New cases vs. Tested in {}".format(s), fontsize=18)

        plt.xticks(rotation=45, fontsize=14)
        plt.bar(dates.values, abs(newtested), width=w, color='cyan', edgecolor='cyan', label="New Tests")
        plt.bar(dates.values + w, newcases, width=w, color='blue', edgecolor='blue', label="New Cases")
        # To set the legend on the plot we have used plt.legend()
        plt.legend()

        plt.subplots_adjust(bottom=0.22)
        plt.grid()
        plt.show()
        print()

        plt.figure(figsize=(13, 7))
        if last_30_days:
            plt.title("New deaths in {}, for last 30 days".format(s), fontsize=18)
        else:
            plt.title("New deaths in {}".format(s), fontsize=18)
        plt.bar(dates.values, newdeaths, color='black', edgecolor='k')
        plt.xticks(rotation=45, fontsize=14)
        plt.grid()
        plt.subplots_adjust(bottom=0.22)
        plt.show()

        if show_tested:
            plt.figure(figsize=(13, 7))
            if last_30_days:
                plt.title("Tested in {}, for last 30 days".format(s), fontsize=18)
            else:
                plt.title("Tested in {}".format(s), fontsize=18)

            plt.bar(dates.values, numtested, color='orange', edgecolor='orange')
            plt.xticks(rotation=45, fontsize=14)
            plt.subplots_adjust(bottom=0.22)
            plt.grid()
            plt.show()
            print()

        plt.figure(figsize=(13, 7))
        if last_30_days:
            plt.title("Recovered in {}, for last 30 days".format(s), fontsize=18)
        else:
            plt.title("Recovered in {}".format(s), fontsize=18)
        plt.bar(dates.values, numrecover, color='green', edgecolor='green')
        plt.xticks(rotation=45, fontsize=14)
        plt.grid()
        plt.subplots_adjust(bottom=0.22)
        plt.show()


    # --------------------------------------------------------------------------------------------------------------
    def plotMultiProvince(self,
                          provinces=None,
                          last_30_days=False,
                          date_500cases=None,
                          date_10deaths=None
                          ):
        """
        Plots multiple provinces data in a single plot for comparison
        """
        from scipy import interpolate
        import time
        def draw_tangent(x, y, a):
            #convert timestamp to seconds to be able to interpolate
            oneday = 3600*24
            xsec = pd.to_datetime(x).astype(np.int64) / 10 ** 9
            asec = time.mktime(a.timetuple())
            spl = interpolate.splrep(xsec, y)
            small_t = np.arange(asec - 5 * oneday, asec + 5 * oneday, step = oneday)
            fa = interpolate.splev(asec, spl, der=0)  # f(a)
            fprime = interpolate.splev(asec, spl, der=1)  # f'(a)
            tan = fa + fprime * (small_t - asec)  # tangent Y=10^(Slope*X + Yintercept)
            xts = datetime.fromtimestamp(asec)
            small_ts = [datetime.fromtimestamp(t.astype(int)) for  t in small_t]

            #calculate the slope
            rate =  (tan[0]/fprime)/oneday
            plt.plot(xts, fa, 'om', small_ts, tan, ':', linewidth=3.5)
            plt.text(small_ts[0],
                     fa + fa/5, 'Doubling time is {:4.1f} days'.format(rate),
                     rotation=2,
                     fontdict={'color': 'red', 'fontsize': 14,
                               'ha': 'center', 'va': 'center'}
                     )

        def plotCountry(dates, cases, title, last_30_days=False,
                        date_500cases_len=None,
                        date_10deaths_len=None,
                        log=False):
            """

            :param dates:
            :param cases:
            :param title:
            :return:
            """

            plt.figure(figsize=(12, 12))
            plt.title(title, fontsize=18)

            if last_30_days == False and date_500cases_len is None and date_10deaths_len is None:
                date = self.countrydict[self.countryName][dates]
                case = self.countrydict[self.countryName][cases]
            elif last_30_days == True:
                date = self.countrydict[self.countryName][dates][-31:-1]
                case = self.countrydict[self.countryName][cases][-31:-1]
            elif date_500cases_len is not None:
                date = self.countrydict[self.countryName][dates][-date_500cases_len:-1]
                case = self.countrydict[self.countryName][cases][-date_500cases_len:-1]
            elif date_10deaths_len is not None:
                date = self.countrydict[self.countryName][dates][-date_10deaths_len:-1]
                case = self.countrydict[self.countryName][cases][-date_10deaths_len:-1]

            if log == False:
                plt.plot(date, case, '-o', color='blue', linewidth=2, markersize=4)
            else:
                if sys.version_info < (3,8):
                    plt.semilogy(date, case, '-', linewidth=3, markersize=4, base=10)
                else:
                    plt.semilogy(date, case, '-', linewidth=3, markersize=4, base=10)

            plt.xticks(rotation=45, fontsize=14)

            legend = [self.countryName]
            if (date_500cases_len is not None and log == True) or \
               (date_10deaths_len is not None and log == True):
                # Plot the 3, 5, 10 and 15 days of doubling the cases
                for rate in [5, 10, 15, 20, 30]:
                    xrange = [x for x in range(0, len(date))]
                    if date_10deaths_len:
                        y_vals = [50 * pow(2, y / rate) for y in xrange]
                    elif date_500cases_len is not None:
                        y_vals = [500 * pow(2, y / rate) for y in xrange]
                    else:
                        print("Wrong set of data!")
                        exit(2)
                    color = tuple(np.round(np.random.random(3), 3))
                    if sys.version_info < (3,8):
                        plt.semilogy(date, y_vals, '--', linewidth=0.5, color=color, base=10)
                    else:
                        plt.semilogy(date, y_vals, '--', linewidth=0.5, color=color, base=10)
                    legend.append("Cases double every %d days" % rate)
                #now draw the tangent
                draw_tangent(date, case, date.iloc[-4])

            plt.legend(legend, fontsize=12)
            plt.grid()
            plt.subplots_adjust(bottom=0.15)
            plt.show()

        def plotSpecificCase(provinces, dates, cases, title, last_30_days=False, log=False):
            """
            :param dates:
            :param cases:
            :param title:
            :return:
            """
            plt.figure(figsize=(12, 12))
            plt.title(title, fontsize=18)

            for s, i in zip(provinces, range(0, len(provinces))):
                if last_30_days == False:
                    date = self.provincedict[s][dates]
                    case = self.provincedict[s][cases]
                else:
                    date = self.provincedict[s][dates][-31:-1]
                    case = self.provincedict[s][cases][-31:-1]
                if log == False:
                    plt.plot(date, case, '-o', color=colors[i], linewidth=2, markersize=4)
                else:
                    if sys.version_info < (3, 8):
                        plt.semilogy(date, case, '-', color=colors[i], linewidth=2, markersize=4, base=10)
                    else:
                        plt.semilogy(date, case, '-', color=colors[i], linewidth=2, markersize=4, base=10)

                plt.xticks(rotation=45, fontsize=14)

            plt.legend(provinces, fontsize=14)
            plt.grid()
            plt.subplots_adjust(bottom=0.15)
            plt.show()


        # main body
        if provinces is None:
            provinces = ['Ontario', 'Quebec', 'British Columbia', 'Alberta']
        provinces = provinces
        colors = []
        for s in provinces:
                color = tuple(np.round(np.random.random(3), 3))
                colors.append(color)

        plotSpecificCase(provinces, 'date', 'totalcases', "Cumulative cases multiprovince", last_30_days)
        plotSpecificCase(provinces,'date', 'totaldeaths', "Cumulative deaths multiprovince", last_30_days)

        if date_500cases is None:
            start = datetime.fromisoformat('2020-03-17')
        else:
            start = date_500cases
        end = datetime.today()
        drange500 = pd.date_range(start=start, end=end)
        lnc = len(drange500)
        if date_10deaths is None:
            start = datetime.fromisoformat('2020-03-22')
        else:
            start = date_10deaths
        end = datetime.today()
        drange10 = pd.date_range(start=start, end=end)
        lnd = len(drange10)-5
        plotCountry('date', 'totalcases', "Cumulative cases Canada since 500 registered cases",
                         last_30_days=False, date_500cases_len=lnc, log=True)
        plotCountry('date', 'totaldeaths', "Cumulative deaths Canada since 50 registered deaths",
                    last_30_days=False, date_10deaths_len=lnd, log=True)
        if False:
            plotSpecificCase(provinces,'date', 'totalcases', "Cumulative cases multiprovince last 30 days",
                         last_30_days=True, log=True)
            plotSpecificCase(provinces,'date', 'totaldeaths', "Cumulative deaths multiprovince last 30 days",
                         last_30_days=True, log=True)


    # --------------------------------------------------------------------------------------------------------------
    def sortProvinces(self, N=5, daterank=None):
        """
        sort in descending order the provinces by categories
        :param N:
        :param daterank:
        :return:
        """

        def fillNaN(sortedlist):
            """

            :return:
            """
            for tup, i in zip(sortedlist, range(0, len(sortedlist))):
                lst = list(tup)
                if math.isnan(lst[0]):
                    lst[0] = 0
                    tp = tuple(lst)
                    sortedlist[i] = tp

            return sortedlist

        from datetime import date
        cases = {}
        deaths = {}
        newcases = {}
        newdeaths = {}

        if daterank is None:
            d = self.countrydf.iloc[-1]['date'].date()
        else:
            d = datetime.datetime.strptime(daterank, '%Y-%m-%d').date()

        for s in self.provincedict:
            df = self.provincedict[s]
            for i in range(len(df)):
                if df['date'].iloc[i].date() == d:
                    cases[s] = df.iloc[i]['totalcases']
                    deaths[s] = df.iloc[i]['totaldeaths']
                    if pd.isna(df.iloc[i]['newcases']):
                        newcases[s] = df.iloc[i - 1]['newcases']
                    else:
                        newcases[s] = df.iloc[i]['newcases']
                    newdeaths[s] = df.iloc[i]['newdeaths']

        sorted_cases = sorted(((value, key) for (key, value) in cases.items()), reverse=True)
        sorted_cases = fillNaN(sorted_cases)
        sorted_cases = sorted_cases[:N]
        sorted_deaths = sorted(((value, key) for (key, value) in deaths.items()), reverse=True)
        sorted_deaths = fillNaN(sorted_deaths)
        sorted_deaths = sorted_deaths[:N]
        sorted_newcases = sorted(((value, key) for (key, value) in newcases.items()), reverse=True)
        sorted_newcases = fillNaN(sorted_newcases)
        sorted_newcases = sorted_newcases[:N]
        sorted_newdeaths = sorted(((value, key) for (key, value) in newdeaths.items()), reverse=True)
        sorted_newdeaths = fillNaN(sorted_newdeaths)
        sorted_newdeaths = sorted_newdeaths[:N]

        return [d, sorted_cases, sorted_deaths, sorted_newcases, sorted_newdeaths]

    # --------------------------------------------------------------------------------------------------------------
    def rankProvince(self,
                     N=5,
                     daterank=None):
        """
        Ranks the provinces in a bar chart
        Arguments:
            N: Top N provinces to be ranked
            date: Date at which the ranking is done.
                  Must be a string in the form '2020-3-27'
                  :param N:
                  :param daterank:
        """

        def plotBar(pos, cases, dt, color, title):
            """
            This plots based base on the time series data
            :param pos:
            :param cases:
            :param dt:
            :param color:
            :param title:
            :return:
            """
            labels = [val[1] for val in cases]
            labels2 = ["Test"] + labels  # this is to overcome a bug in the bar function
            x = np.arange(len(labels))  # the label locations
            axs[pos].bar(x, [val[0] for val in cases], color=color, edgecolor=color)
            axs[pos].set_title("{} on {}".format(title, str(dt)), fontsize=15)
            axs[pos].xaxis.set_major_locator(plt.FixedLocator(x))
            axs[pos].xaxis.set_major_formatter(plt.FixedFormatter(labels))
            #axs[pos].set_xticklabels(labels2)
            axs[pos].grid(axis="y")
            plt.setp(axs[pos].xaxis.get_majorticklabels(), rotation=35, fontsize=12)

        res = self.sortProvinces(N=N)
        [dt, sorted_cases, sorted_deaths, sorted_newcases, sorted_newdeaths] = res

        # fill the nans with Zero to avoid screwing up the bars

        fig, axs = plt.subplots(2, 2, figsize=(13, 12))
        axs = axs.ravel()
        plotBar(0, sorted_cases, dt, 'blue', "Total cases")
        plotBar(1, sorted_deaths, dt, 'red', "Total deaths")
        plotBar(2, sorted_newcases, dt, 'yellow', "New cases")
        plotBar(3, sorted_newdeaths, dt, 'orange', "New deaths")
        plt.subplots_adjust(wspace=0.2, hspace=0.6)
        fig.tight_layout()

        plt.show()


    # --------------------------------------------------------------------------------------------------------------
    def rateOfChange(self,
                     provinces=None,
                     WINDOW=5,
                     last_30_days=True):
        """
        calculates daily date of change from data
        """
        if not self._processed:
            print("Data not processed yet. Cannot plot countrywise.")
            return None

        if provinces is None:
            provinces = ['Ontario', 'Quebec', 'British Columbia', 'Alberta']
        plt.figure(figsize=(13, 7))
        colors = []
        for s in provinces:
            df = self.provincedict[s]
            df["cases_rtc"] = df['totalcases'].pct_change(fill_method='ffill')
            # if pd.isna(df["cases_rtc"]).any():
            #    df["cases_rtc"] = df["cases_rtc"].fillna(0)

            color = tuple(np.round(np.random.random(3), 3))
            colors.append(color)
            if last_30_days:
                plt.plot(self.provincedict[s]['date'][-31:-1],
                         df["cases_rtc"][-31:-1] * 100,
                         color=color,
                         linewidth=2)
            else:
                plt.plot(self.provincedict[s]['date'],
                         df["cases_rtc"] * 100,
                         color=color,
                         linewidth=2)

        plt.title("Rate of change total cases in [%]", fontsize=15)
        plt.legend(provinces, fontsize=14)
        plt.xticks(rotation=45, fontsize=14)
        plt.subplots_adjust(bottom=0.22)
        plt.grid()
        plt.show()

        plt.figure(figsize=(13, 7))
        for s, color in zip(provinces, colors):
            df = self.provincedict[s]
            df["deaths_rtc"] = df['totaldeaths'].pct_change()  # fill_method='ffill')
            # if pd.isna(df["deaths_rtc"]).any():
            #    df["deaths_rtc"] = df["deaths_rtc"].fillna(0)
            if last_30_days:
                plt.plot(self.provincedict[s]['date'][-31:-1],
                         df["deaths_rtc"][-31:-1] * 100,
                         color=color,
                         linewidth=2)
            else:
                plt.plot(self.provincedict[s]['date'],
                         df["deaths_rtc"] * 100,
                         color=color,
                         linewidth=2)

        plt.xticks(rotation=45, fontsize=14)
        plt.grid()
        plt.title("Rate of change total deaths in [%]", fontsize=15)
        plt.legend(provinces, fontsize=14)
        plt.subplots_adjust(bottom=0.22)
        plt.show()
        # average for the last WINDOW periods
        lcases_rtc = df["cases_rtc"][-WINDOW:]
        ldeaths_rtc = df["deaths_rtc"][-WINDOW:]
        return (lcases_rtc.mean(), ldeaths_rtc.mean())


    # --------------------------------------------------------------------------------------------------------------
    def scenarioPrediction(self, rateWINDOW=5, time_int=30, provinces=None, dateprog=None):
        """
        Based on current average daily
        :return:
        """

        def compoundInterest(principle, rate, time):
            result = []
            index = [i for i in range(0, time)]
            base = principle  # .values[0]
            for t in range(0, time):
                result.append(base * (pow((1 + rate), t + 1)))

            pred_cases = pd.Series(result, index=index)
            return pred_cases

        (case_rt, death_rt) = self.rateOfChange(WINDOW=rateWINDOW, last_30_days=True)

        if provinces is None:
            provinces = ['Ontario', 'Quebec', 'British Columbia', 'Alberta']
        provinces = provinces

        if dateprog is None:
            d = self.countrydf.iloc[-1]['date'].date()
        else:
            d = datetime.datetime.strptime(dateprog, '%Y-%m-%d').date()

        plt.figure(figsize=(13, 7))
        plt.title("No Social distancing Prediction Scenario - daily new cases", fontsize=15)
        colors = []
        for s in provinces:
            color = tuple(np.round(np.random.random(3), 3))
            colors.append(color)
            dates = self.provincedict[s]['date']

            if pd.isna(self.provincedict[s]['newcases'].iloc[-1]):
                newcases = self.provincedict[s]['newcases'].iloc[:-1]
            else:
                newcases = self.provincedict[s]['newcases']
            prednewcases = compoundInterest(newcases.tail(3).mean(), case_rt, time_int)

            date_today = datetime.now()
            days = pd.date_range(date_today, date_today + timedelta(time_int - 1), freq='D')
            df = pd.DataFrame({'test': days, 'casepred': prednewcases})
            df = df.set_index('test')

            plt.plot(df.index,
                     df['casepred'],
                     color=color,
                     linewidth=2)

        plt.xticks(rotation=45, fontsize=14)
        plt.legend(provinces, fontsize=14)
        plt.grid()
        plt.subplots_adjust(bottom=0.22)
        plt.show()

        plt.figure(figsize=(13, 7))
        plt.title("No Social distancing -Prediction scenario- daily new deaths", fontsize=15)
        colors = []
        for s in provinces:
            color = tuple(np.round(np.random.random(3), 3))
            colors.append(color)
            dates = self.provincedict[s]['date']
            newdeaths = self.provincedict[s]['newdeaths']
            prednewdeaths = compoundInterest(newdeaths.tail(3).mean(), case_rt, time_int)

            date_today = datetime.now()
            days = pd.date_range(date_today, date_today + timedelta(time_int - 1), freq='D')
            df = pd.DataFrame({'test': days, 'deathpred': prednewdeaths})
            df = df.set_index('test')

            plt.plot(df.index,
                     df['deathpred'],
                     color=color,
                     linewidth=2)

        plt.xticks(rotation=45, fontsize=14)
        plt.legend(provinces, fontsize=14)
        plt.grid()
        plt.subplots_adjust(bottom=0.22)
        plt.show()