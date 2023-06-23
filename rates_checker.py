import requests
from bs4 import BeautifulSoup
import json
import time
import smtplib


def request_with_retries(method, **kargs):
    retries = 0
    max_retries = 3
    if "max_retries" in kargs:
        max_retries = kargs.pop("max_retries")

    while retries < max_retries:
        try:
            resp = requests.request(method=method, **kargs)
            if resp.status_code == 429 and "Retry-After" in resp.headers:
                retry_secs = int(resp.headers["Retry-After"])
                try:
                    print(f"Got Retry-After header in response. Retrying after {retry_secs}")
                    time.sleep(retry_secs)
                except OverflowError as o:
                    print(f"Got Retry-After header in response. Retrying after {retry_secs}")
                    time.sleep(4)

            elif resp.status_code == 200:
                return resp
            else:
                raise Exception(f"Status: {resp.status_code}, message: {resp.content}")
        except Exception as e:
            print(f"Got Error during search: {str(e)}")
            print("Retrying......")
            retries += 1
            if retries == max_retries - 1:
                print(f"Got Error during search: {e}")
            return resp

def get_data_from_url(url):
    html_text = request_with_retries("GET", url=url).text
    soup = BeautifulSoup(html_text, 'html.parser')
    current_rates = {}

    date_text = soup.find("div", {"class": "deck__detail col-md-12 tpgr-body--m"})\
                        .find("strong").text.split("\n")[0]
    print(date_text)
    current_rates["date"] = date_text
    current_rates["rates"] = {}

    for li in soup.findAll("li", {"class": "col-xs-12 col-md-6 card__block"}):
        title = li.find("h3").text.strip()
        current_rates["rates"][title] = {}
        for tag in li.findAll("strong"):
            tag_text = tag.text.strip()
            if "arm" in tag_text.lower():
                current_rates["rates"][title]["arm"] = tag_text
            elif "apr" in tag_text.lower():
                current_rates["rates"][title]["rate_apr"] = tag_text
            else:
                current_rates["rates"][title]["rate"] = tag_text

    print(current_rates)
    return current_rates

def send_mail(current_date):

    mailserver = smtplib.SMTP('mailhost@schwab.com', 25)
    mailserver.connect('mailhost@schwab.com', 25)
    msg = "Featured mortgage rates date : " + current_date
    mailserver.sendmail('yshardul@gmail.com', f"\n{msg}")
    mailserver.quit()

def process_rates():
    current_rates = get_data_from_url("https://www.schwab.com/mortgages/mortgage-rates")
    json.dump(current_rates, open("prev_rates.json", "w"), indent=4)
    send_mail(current_rates["date"])


process_rates()


