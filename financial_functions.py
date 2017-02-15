# -*- coding: utf-8 -*-

# %% 
import numpy as np
from datetime import datetime, date

# %% 
def toDate(datetime_obj):
    '''toDate function
    Transforms a datetime object to date. 
    '''
    return date(datetime_obj.year, datetime_obj.month, datetime_obj.day)

# %% Basic financial functions

# future_value
futureValue = lambda capital, interest, periods: capital * (1 + interest) ** periods
contFutureValue = lambda capital, interest, years: capital * np.exp(interest * years)

# present_value 
presetValue = lambda capital, interest, periods: capital * (1 + interest) ** (-periods)
contPresentValue = lambda capital, interest, years: capital * np.exp(-interest * years)

# annual interest rate
annualInterest = lambda initial_capital, end_capital, years: (end_capital / initial_capital) ** (1 / years) - 1

# %% Other financial functions 

# equivalent annual interest rate
'''equivalentAnnualInterest function
This function returns the equivalent annual interest rate with 1y capitalization
for a given interest rate (rate) with cap-capitalizations per year. 

---- inputs
rate: previous annual interest rate
cap: number of time the prev. rete capitalizes per year

--- outputs 
An equivalent annual rate that capitalizes 1 time per year.
'''
equivalentAnnualInterest = lambda rate, cap: (1 + rate / cap) ** cap - 1 

# equivalent rate 
'''equivalentRate function
This function returns an annual interest rate with new_cap-capitalizations per year given
a previous annual rate (rate) with cap-capitalizations per year

---- inputs 
rate:
cap:
new_cap:

---- outputs
...
'''
equivalentRate = lambda rate, cap, new_cap: new_cap * ((1 + rate / cap) ** (cap / new_cap) - 1)

realRate = lambda rate, inflation: (1+rate)/(1+inflation) - 1
# %% Risk Free Interest Rate (CETES)

def getRiskFreeRate():
    '''getRiskFreeRate function.
    description: This fuction returns the risk-free interest rate (cetes) for 28,91,182 days.
    
    ---- inputs
     
    
    ---- outputs
    
    
    '''
    
    # import libraries
    import urllib.request
    
    # open url to get source
    with urllib.request.urlopen('http://www.banxico.org.mx/SieInternet/'+
                                'consultarDirectorioInternetAction.do?a'+
                                'ccion=consultarCuadro&idCuadro=CF107&s'+
                                'ector=22&locale=es') as response:
        
        # read source and save as string 
        html_source = response.read().decode('latin-1')
    
    
    # identify target
    def getTarget(source):
        '''getTarget function
        description: function adapted to retrieve the value of cetes interest rate. 
        
        ---- inputs
        source: 
        
        ---- outputs
        position_index: 
        value: 
        
        '''
        
        tasa_de_rendimiento = source.find('Tasa de rendimiento')
        visibility_hidden   = 0
        
        for i in range(3):
            visibility_hidden += source[tasa_de_rendimiento:][visibility_hidden:].find('<span style="visibility:hidden">')+34
            
        position_index = tasa_de_rendimiento + visibility_hidden - 10 - 34
        value          = float(source[position_index:position_index+10].strip(' '))
        return position_index, value

    
    # get key,values and save in dictionary 
    cetes_dictionary = {}
    reference_index  = 0
    
    for i in [28, 91, 182]:
        html_source            = html_source[reference_index:]
        reference_index, value = getTarget(html_source)
        cetes_dictionary[i]    = value
    
    
    return cetes_dictionary

# %% Interest Rate class 

class interest_rate:
    
    # basic description and references
    desc          = 'Interest Rate Object'
    cap_options   = {'daily':360, '1m':12, '2m':6, '3m':4, '4m':3, '6m':2, '1y':1, 'cont':float('inf')}
    cetes         = getRiskFreeRate()
    
    
    # init class 
    def __init__(self, rate = {'rate':0.12, 'cap':12}):
        self.reference_rate = rate
    
    def annualRate(self, cap_desc):
        '''calulate_equivalent method
        Use the reference_rate to calculate different equivalent rates. 
        Specif: daily, monthly, 2-months, 3-months, 4-months, 6-months, 1y, continuously
        '''
        
        # get capitalization frequency
        if type(cap_desc) == type(' '):
            aux = self.cap_options[cap_desc]
        elif type(cap_desc) == type(1):
            aux = cap_desc
        
        if cap_desc == 'cont':
            return contEquivalentRate(self.reference_rate['rate'], self.reference_rate['cap'])
        
        return equivalentRate(self.reference_rate['rate'], self.reference_rate['cap'], aux)
        

    def rate(self, cap_desc):
        '''rate method
        Use equivalentRate to generate a ready-to-use rate.
        '''
        
        # get capitalization frequency
        if type(cap_desc) == type(' '):
            aux = self.cap_options[cap_desc]
        elif type(cap_desc) == type(1):
            aux = cap_desc
        
        if cap_desc == 'cont':
            return self.annualRate(cap_desc)
        
        return self.annualRate(cap_desc) / aux
    
    def riskFreeSpread(self, risk_free = 28, silence = False, kind = 'cont'):
        '''riskFreeSpread function
        Calculate the spread between the risk free interest rate and the pacted interest rate.
        kind = ['cont','eq_annual']
        '''
        
        # catch error 
        # TODO: check if risk_free is on cetes.keys()
        
        if kind == 'cont':
            r  = contEquivalentRate(self.reference_rate['rate'], self.reference_rate['cap'])
            rf = contEquivalentRate(self.cetes[risk_free] / 100, 360/risk_free)
            if not silence:
                print('Decimal spread for equivalent continuos interest ({:.2f}% - {:.2f}%): {}'.format(100*r, 100*rf,r - rf))
            return r - rf 
        
        r  = equivalentAnnualInterest(self.reference_rate['rate'], self.reference_rate['cap'])
        rf = equivalentAnnualInterest(self.cetes[risk_free] / 100, 360/risk_free)
        if not silence:
            print('Decimal spread for equivalent annual interest ({:.2f}% - {:.2f}%): {}'.format(100*r, 100*rf,r - rf))
        return r - rf 
    

# %% Debt class

class debt:

    desc = 'Interest Rate Object'
    rate_options  = {360:'daily', 12:'1m', 6:'2m', 4:'3m', 3:'4m', 2:'6m', 1:'1y'}
    cap_options   = {'daily':360, '1m':12, '2m':6, '3m':4, '4m':3, '6m':2, '1y':1}
    cetes         = getRiskFreeRate()

    def __init__(self, initial_date, final_date,capital = 10000, rate = {'rate':0.12, 'cap':12}, discount_rate = 28):
            
        self.payments = []
        self.invalid_payments = []
        
        # dates 
        self.initial_date   = toDate(datetime.strptime(initial_date, '%b %d %Y'))
        self.final_date     = toDate(datetime.strptime(final_date, '%b %d %Y'))
        self.actual_date    = toDate(datetime.now())
            
        self.initial_date_string = initial_date
        self.final_date_string   = final_date

        # capital 
        self.capital = capital

        # rate 
        self.reference_rate = rate
        self.i = interest_rate(self.reference_rate)

        self.final_capital  = round(futureValue(capital, self.i.rate(360), (self.final_date - self.initial_date).days), 2)

        # discount rate
        # TODO: validate 

        self.discount_rate = interest_rate({'rate':self.cetes[discount_rate]/100, 'cap':360/discount_rate})
    
    def daysToGo(self, ref_date = None):
        '''daysToGo functions 
        Returns the days between actual_date and final_date 
        '''
        if type(ref_date) == type(None):
            ref_date = self.actual_date
        
        if type(ref_date) == type(''):
            ref_date = toDate(datetime.strptime(ref_date, '%b %d %Y'))
        
        return (self.final_date - ref_date).days

    
    def diffDates(self, date0, date1):
        '''diffDates
        Returns the diff betwenn two dates
        '''
        date0 = toDate(datetime.strptime(date0, '%b %d %Y'))
        date1 = toDate(datetime.strptime(date1, '%b %d %Y'))
        return (date1-date0).days

    def discountRate(self, cap_desc):
        '''discountRate function
        Use discountRate function to get the discount interest rate for...
        '''
        
        return self.discount_rate.rate(cap_desc)
    
    def registerPayment(self, amount, date = 'now'):
        '''registerPayment function
        add description
        '''
        
        if 'now' in date:
            date = datetime.strftime(datetime.now(), '%b %d %Y')
        
        if len(self.payments) == 0:
            self.payments.append({'id':1,'date':date,'amount':amount,'valid':True})
        else:
            new_id = self.payments[-1]['id'] + 1
            self.payments.append({'id':new_id,'date':date,'amount':amount,'valid':True})
    
    def invalidPayments(self, _id):
        '''invalidPayments function
        '''
        self.invalid_payments.append(_id)
        
        if len(self.payments) != 0:
            for _index in range(len(self.payments)):
                if self.payments[_index]['id'] in self.invalid_payments:
                    self.payments[_index]['valid'] = False
                    
    def deleteInvalidPayment(self, _id):
        '''deleteInvalidPayment function
        '''
        ip = []
        for i in self.invalid_payments:
            if i != _id:
                ip.append(i)
                
        if len(self.payments) != 0:
            for _index in range(len(self.payments)):
                if self.payments[_index]['id'] == _id:
                    self.payments[_index]['valid'] = True  
                    
        self.invalid_payments = ip
        
    def resetInvalidPayments(self):
        '''resetInvalidPayments function
        '''
        self.invalid_payments = []
        # TODO: update payment status
        
    def resetPayments(self):
        '''resetPayments function
        Reset payments.
        '''
        self.payments = []
    
    
    def actualFinalDebt(self):
        '''actualFinalDebt function
        '''
        
        if len(self.payments) == 0:
            return self.final_capital
        
        total = 0
        for _index in range(len(self.payments)):
            
            if not self.payments[_index]['valid']:
                continue
                
            _date = self.payments[_index]['date']
            _amount = self.payments[_index]['amount']
            _delta  = self.daysToGo(_date)
            _future = futureValue(_amount, self.discountRate('daily'), _delta)
            total += _future
        
        actual_debt = self.final_capital - total
        
        if actual_debt < 0:
            return 0
            
        return actual_debt

    def actualPresentDebt(self):
        '''actualPresentDebt function 
        '''
        afd = self.actualFinalDebt()
        return presetValue(afd, self.discountRate('daily'), self.daysToGo())
    
    def payDebt(self, pay_date = None):
        '''payDebt function
        Calculate the debt value (present value of final_capital using discount rate) to a given time. 
        '''
        
        if type(pay_date) == type(None):
            pay_date = toDate(datetime.now())
        else:
            pay_date = toDate(datetime.strptime(pay_date, '%b %d %Y'))
        
        # get dates 
        days = self.daysToGo(ref_date = pay_date)
        
        # get discount 
        dr = self.discountRate('daily')
        
        # return present value
        return presetValue(self.actualFinalDebt(),dr, days)
        
    
    def simulate(self, periods = 1, cap_desc = '1y', initial_capital = ''):
        '''simulate function
        Simulate debt growth (with pacted interest rate) for n-periods accordig to cap_desc. 
        '''
        
        if type(initial_capital) == type(''):
            initial_capital = self.capital
        
        return futureValue(initial_capital, self.rate(cap_desc), periods)
    
    def simulateYears(self, years = 1, cap_desc = '1y', initial_capital = ''):
        '''simulatYears function
        Simulate debt growth (with pacted interest rate) for n-years according to cap_desc. 
        '''
        
        if type(initial_capital) == type(''):
            initial_capital = self.capital
            
        return futureValue(initial_capital, self.rate(cap_desc), years * self.cap_options[cap_desc])

    def simulateMonths(self, months = 1, cap_desc = '1y', initial_capital = ''):
        '''simulateMonths function 
        Simulate debt growth (with pacted interest rate) for n-months according to cap_desc.
        '''
        
        if type(initial_capital) == type(''):
            initial_capital = self.capital
        
        return self.simulateYears(initial_capital, months / 12, cap_desc)
    
    def status(self, silence = True):
        '''status function
        '''
        
        flag = self.daysToGo()
        
        if self.actualFinalDebt() == 0:
            self.debt_status = 'Done.'
        if flag < 0 and self.actualFinalDebt() > 0:
            self.debt_status = 'Overdue.'
        if flag > 0 and self.actualFinalDebt() > 0:
            self.debt_status = 'Active.'
            
        if not silence:
            print(self.debt_status)
            
        return self.debt_status
    
    def summary(self):
        '''summary function
        '''
        print(datetime.strftime(datetime.now(),'%b %d %Y'))
        
        st = '\nStatus: {}\nDays to go: {}\n\nInitial Capital: {}\nFinal Capital  : {}\nInterest Rate (cont. annual): {:.4f} %\n'
        ri = 'Discount Rate (cont. annual): {:.4f} %\n\nRemaining Debt: {}\nPresent Value : {}\n'
        ng = '\nPayments info: \n'
        
        for i in range(len(self.payments)):
            if not self.payments[i]['valid']:
                continue 
            ng+='\n- id: {} date: {} amount: {}'.format(self.payments[i]['id'],
                                                        self.payments[i]['date'], 
                                                        self.payments[i]['amount'])
        
        st = st.format(self.status(), self.daysToGo() , self.capital, self.final_capital, 100*self.i.rate('cont'))
        ri = ri.format(100*self.discountRate('cont'),round(self.actualFinalDebt(),2), round(self.actualPresentDebt(),2))
        #ng = ng.format()
        
        print(st+ri+ng)
        
    def save(self, active = False):
        '''save function
        '''
        
        if active:
            import query_module.query_functions as qm
            db_path = ''
            pass
        
        pass
    
    def update(self, active = False):
        '''update function
        '''
        
        if active: 
            import query_module.query_functions as qm
            db_path = ''
            pass 
        
        pass
        
        
    
    
        

# %% BONDS 

class Bonds(object):
    desc = 'Generic Bonds'
    rate_options  = {360:'daily', 12:'1m', 6:'2m', 4:'3m', 3:'4m', 2:'6m', 1:'1y'}
    cap_options   = {'daily':360, '1m':12, '2m':6, '3m':4, '4m':3, '6m':2, '1y':1}
    #cetes         = getRiskFreeRate()
    
    def __init__(self,nominal_value=100,coupons={'delta_periods':182,'interest_rate':0.082},
                 market_rate=0.085,time2maturity=100):
        
        self.nominal_value = nominal_value
        
        # Coupon related info
        self.coupons = coupons
        self.coupons['value'] = nominal_value*coupons['delta_periods']*coupons['interest_rate'] / 360
        self.coupons['pending_coupons'] = time2maturity / coupons['delta_periods']
        self.coupons['integer_coupons'] = int(self.coupons['pending_coupons'])
        self.coupons['float_coupons']   = self.coupons['pending_coupons'] - self.coupons['integer_coupons']
    
        # interest rate
        self.market_rate = market_rate
        
        # passed days
        self.passed_units  = self.coupons['delta_periods']*(1-self.coupons['float_coupons'])
        self.pending_units = self.coupons['float_coupons']*self.coupons['delta_periods']
        
        self.market_rate = market_rate

    def dirtyPrice(self):
        present_value_list = []
        for i in range(self.coupons['integer_coupons']):
            j = i + 1
            present_value_list.append(presetValue(self.coupons['value'] if j != self.coupons['integer_coupons'] else self.coupons['value']+self.nominal_value,
                                         self.coupons['delta_periods']*self.market_rate/360,j))
        self.lsp = present_value_list
        present_value = sum(present_value_list)
        if self.coupons['float_coupons'] == False:
            return present_value
        return present_value+self.coupons['value']
    
    def cleanPrice(self):
        
        self.dirty_price = self.dirtyPrice()
        if self.coupons['float_coupons'] == False:
            return self.dirty_price
        value_at_passed = self.dirty_price / (1+self.coupons['delta_periods']*self.market_rate/360)**(self.pending_units/self.coupons['delta_periods'])
        self.delayed_interest = self.nominal_value*self.coupons['interest_rate']*self.passed_units/360
        self.clean_price = value_at_passed - self.delayed_interest
        return self.clean_price
        
    def getDuration(self):
        duration, c = 0, 1
        for i in self.lsp:
            duration += c*self.coupons['delta_periods']*i/360
            c += 1
        self.duration = duration / self.cleanPrice()
        return self.duration
        
    def getSensibility(self):
        return self.getDuration() / (1+self.market_rate)

# %% 

# %%

# %%

# %%

# %%