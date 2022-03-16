# Finance

Finance is a python-based web applet that uses Flask which you can manage portfolios of stocks. Not only will this tool allow you to check real stocks’ actual prices and portfolios’ values, it will also let you simulate buying and selling stocks by querying IEX for stocks’ prices. In order to access IEX, you must visit [iexcloud](https://iexcloud.io/cloud-login#/register/) and copy the key under the token column after account creation and run 
```console
$ export API_KEY=value 
```
in terminal where value is the key copied (example key: pk_bee99a518e224fc4a009acba7198c9cb). After that, all you have to do is run 
```console
$ flask run 
```
and go to the link created for you to interact with the site.

### Features

First and foremost, there is a login page and a registration page. Once you register an account, you will be able to log in with those credentials and access the rest of the site. There are 6 main pages you can access on this web app:
- Home Page
- Quote
- Buy
- Sell
- History
- Extra Cash

#### Home Page

The Home page displays all the stocks the user owns and the remaining balance they have.

#### Quote

The Quote page allows the user to be able to query any stock's price they so choose. As long as the right symbol is entered, the price of that stock will be returned. However, it does not work for the actual names of the stocks.

#### Buy

The Buy page allows the user to simulate buying any quantity of any stock, so long as they still have a positive balance remaining. 

#### Sell

The Sell page allows the user to simulate selling any amount of stock that has already been purchased, but you cannot sell any more of a stock than you already own. 

#### History

The History page displays all of the transactions that have been processed. This includes all stocks purchased and all stocks sold, including the time of each transaction. 

#### Extra Cash

The Extra Cash page allows the user to add any amount of money they wish to their remaining balance. 
