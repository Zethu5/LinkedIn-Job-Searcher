import json
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re


def init_selenium_browser():
    chrome_options = Options()
    # keep chrome open when finished
    chrome_options.add_experimental_option("detach", True)
    # disable irrelevant eror msgs
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    return webdriver.Chrome(options=chrome_options)


def login_to_linkedin(driver):
    with open('config.json', 'r') as f:
        data = json.load(f)

    driver.get('https://www.linkedin.com/login')

    try:
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, 'username')))
        username_element = driver.find_element(by=By.ID, value='username')
        password_element = driver.find_element(by=By.ID, value='password')
        login_button_div_container = driver.find_element(by=By.CLASS_NAME, value='login__form_action_container')
        login_button_element = login_button_div_container.find_element(by=By.TAG_NAME, value='button')

        username_element.send_keys(data['username'])
        password_element.send_keys(data['password'])
        login_button_element.click()
    except:
        raise Exception("[ERROR] Couldn't log in...")

    WebDriverWait(driver, 10).until(EC.title_contains("Feed | LinkedIn"))


def get_job_id_from_job_element(job_element):
    return job_element.get_attribute('data-occludable-job-id')


def get_job_ids(url, driver):
    job_ids = []

    driver.get(url)
    sleep(5) # get all jobs loaded for page (it's async)

    jobs_elements = driver.find_elements(by=By.CLASS_NAME, value='jobs-search-results__list-item')

    for job_element in jobs_elements:
        job_ids.append(get_job_id_from_job_element(job_element))

    return job_ids


def check_if_viable_job(job_title, job_description):
    requiremenets_regex_array = [r'at least \d years?', r'\d+\+? years?', r'\+\d+ years?', r'[^0]\s?-\s?\d+', r'[^0] to \d+']

    if re.findall('senior', job_title, re.IGNORECASE):
        return {'check': False, 'reason': job_title}

    job_description = job_description.split('\n')
    for line in job_description:
        for reg in requiremenets_regex_array:
            if re.findall(reg, line, re.IGNORECASE):
                return {'check': False, 'reason': line}
    return {'check': True, 'reason': ''}


def get_jobs_data(job_ids, driver, url):
    jobs = []

    for job_id in job_ids:
        driver.get(f'{url}&currentJobId={job_id}')
        try:
            sleep(1)
            WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.CLASS_NAME, 'jobs-description__content')))
            WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.CLASS_NAME, 'jobs-unified-top-card__company-name')))
        except:
            continue

        job_title_element = driver.find_element(by=By.CLASS_NAME, value='jobs-unified-top-card__job-title')
        job_title = job_title_element.text
        job_url = job_title_element.find_element(by=By.XPATH, value='..').get_attribute('href')
        
        company_info = driver.find_element(by=By.CLASS_NAME, value='jobs-unified-top-card__company-name')
        company_info_link = company_info.find_element(by=By.TAG_NAME, value='a')
        company_name = company_info_link.text
        job_description = driver.find_element(by=By.CLASS_NAME, value='jobs-description__content').text.replace('\\n', '\n')

        print(f'-------------------- Checking {job_id} | {job_title} | {company_name} --------------------')

        job_viable_results = check_if_viable_job(job_title, job_description)

        if job_viable_results['check']:
            print('[V] Viable job\n')
            jobs.append(job_url)
        else:
            print(f'[X] Not viable job, reason:\n{job_viable_results["reason"]}\n')
    return jobs



def init(num_pages=10):
    jobs = []
    driver = init_selenium_browser()
    login_to_linkedin(driver)

    # +1 to include the last page
    for index in range(num_pages + 1):
        # each jobs page has 25 jobs
        url = f'https://www.linkedin.com/jobs/search/?f_F=eng&f_JT=F&f_WT=1%2C3&geoId=101620260&location=Israel&sortBy=R&start={index * 25}'
        job_ids = get_job_ids(url, driver)
        jobs.append(get_jobs_data(job_ids, driver, url))
        break

    print('Jobs found:\n')
    print(jobs)


if __name__ == '__main__':
    init()