from scrapy.item import Item
from scrapy.item import Field
from scrapy.spiders import CrawlSpider, Rule
from scrapy.loader import ItemLoader
#from scrapy.linkextractors import LinkExtractor
#from scrapy.selector import Selector
from bs4 import BeautifulSoup
import re, random
from time import sleep
###############################################################
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# NOTE: SINCE THE DATA FROM THE WHOLE PAGE ISN'T IN THE MAIN HTML TREE, WE NEED TO USE "SELENIUM" TOO.

# Defining our class where we'll store our data:
class Course(Item):
    Course_Name = Field(output_processor = lambda x: x[0])
    Description = Field(output_processor = lambda x: x[0])
    Score = Field(output_processor = lambda x: x[0])
    Students = Field(output_processor = lambda x: x[0]) # Number of students in the course.
    Num_of_Ratings = Field(output_processor = lambda x: x[0]) # Number of ratings that the course has.
    Duration_in_hrs = Field(output_processor = lambda x: x[0])
    Price = Field(output_processor = lambda x: x[0])

# Defining our crawler spider:
class UdemyCrawlerSpider(CrawlSpider):
    name = "UdemyCrawlerSpider"
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/84.0.2",
        "FEED_EXPORT_ENCODING": "utf-8",
    }
    allowed_domains = ["udemy.com"]
    start_urls = ["https://www.udemy.com/courses/search/?src=ukw&q=Web+Scraping"]

    """
    # WE CANNOT USE RULES DUE TO THE WAY DATA LOADS ON UDEMY. IF GO TO THE TOOLS OF THE PAGE WE WILL SEE THAT DATA WE ARE
    # SEARCHING FOR ISN'T IN THE MAIN HTML_TREE OF EVERY PAGE, SO, SINCE THE "PATTERNS" WE ARE LOOKING FOR USING "allow" 
    # INSIDE EVERY "RULE", WE ARE NOT GOING TO BE ABLE TO ACCESS TO PAGES AND EVERY COURSE.
    
    rules = (
        Rule(  # HORIZONTAL RULE. Using this rule we will make the PAGINATION.
            LinkExtractor(
                allow=r"p=\d+&q=Web\+Scraping",
            ), follow=True
        ),
        Rule( # VERTICAL RULE. Using this Rule, we will enter to every course and EXTRACT THE DATA.
            LinkExtractor(
                allow = r"/course/",
                restrict_xpaths=["//a[@query]"],
            ), follow=True, callback="parse_course"
        ),
    )
    """

    def formatting_quantities(self, number):

        formated_number = number.replace('.','') if '.' in number else number
        return formated_number

    def parse_start_url(self, response):

        # SELENIUM:
        opts = Options()
        ua = "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/88.0.4324.96 Chrome/88.0.4324.96 Safari/537.36"
        opts.add_argument(ua)
        driver = webdriver.Chrome(".././chromedriver.exe", options=opts)
        driver.get(self.start_urls[0])

        pagination, pages = 50, 1 # "50" pages to visit. Let's start with the "1st" one.
        while pages <= pagination:

            sleep(random.uniform(1.5, 3.5)) # Since Udemy changed its html tree per course due to it started to detected we were doing "Web Scraping".
            WebDriverWait(driver, 10).until( # We wait up to 10 seconds for the pagination to load. Once it has loaded we proceed with the program.
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'pagination--container')]"))
            )
            courses = WebDriverWait(driver, 10).until( # We wait up to 10 seconds for the courses. Once they have loaded, we retrieve them.
                EC.presence_of_all_elements_located((By.XPATH, "//a[@query]"))
            )
            courses = [course_link.get_attribute("href") for course_link in courses] # We obtain the "href" attribute from every course to obtain the link.
            for course_link in courses:

                try:
                    sleep(random.uniform(0.5, 1.5)) # Since Udemy changed its html tree per course due to it started to detected we were doing "Web Scraping".
                    driver.get(course_link)
                    WebDriverWait(driver, 10).until( # Waiting up to 10 seconds for the data to be ready.
                        EC.presence_of_element_located((By.XPATH, "//div[@class='udlite-text-sm clp-lead']"))
                    )
                    WebDriverWait(driver, 10).until( # We wait up to 10 seconds for the price/shopping container to load.
                        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'sidebar-container--purchase-section')]\
                        //div[contains(@class, 'price-text--price-part')]"))
                    )
                    WebDriverWait(driver, 10).until( # We wait up to 10 seconds for the time duration container to load.
                        EC.presence_of_element_located((By.XPATH, "//span[@data-purpose='video-content-length']"))
                    )
                except Exception as e:
                    print("¡Something went wrong with this course. The error is the following:")
                    print(e)
                    print("Let's try with the next one.")
                else:
                    # ALGORITHM TO RETRIEVE DATA:
                    sleep(random.uniform(1.5,2.5))  # Since Udemy changed its html tree per course due to it started to detected we were doing "Web Scraping".
                    BS_object = BeautifulSoup(driver.page_source, "lxml") # We retrieve the "html tree" from the course and we turn it into a BS object.
                    # Course Name:
                    course_name = BS_object.find("h1").get_text().replace('\n','').strip()
                    # Description:
                    description_name = BS_object.find("div",{"class":"udlite-text-md clp-lead__headline"}).get_text()
                    description_name = description_name.replace('\n','').replace('\r','').replace('\t','').strip()
                    # Score:
                    score = BS_object.find("div", {"class":"ud-component--course-landing-page-udlite--rating"})
                    score = float(score.find("span", {"class":re.compile(r"star-rating--rating-number")}).text.strip().replace(',','.'))
                    # Number of students enrolled in the course:
                    number_of_students = BS_object.find("div",{"class":'', "data-purpose":"enrollment"}).text.strip()
                    numbs = ''
                    for i in filter(lambda x: x.isdigit() or x == '.', number_of_students):
                        numbs += i
                    number_of_students = float(self.formatting_quantities(numbs))
                    # Number of ratings given by students to the current course:
                    "//div[contains(@class, 'styles--rating-wrapper')]/text()[last()]"
                    number_of_ratings = BS_object.find("div",{"class":re.compile(r"styles--rating-wrapper")}).get_text().split('(')[-1]
                    numbers = ''
                    for i in filter(lambda x: x.isdigit() or x == '.', number_of_ratings):
                        numbers += i
                    number_of_ratings = float(self.formatting_quantities(numbers))
                    # Duration_in_hrs:
                    duration = BS_object.find("span", {"data-purpose":"video-content-length"}).get_text().replace(',','.')
                    numbers = ''
                    for i in filter(lambda x: x.isdigit() or x == '.', duration):
                        numbers += i
                    duration = float(numbers)
                    # Price:
                    price = BS_object.find("div",{"class":re.compile(r"sidebar-container--purchase-section")})
                    price = price.find("div",{"class":re.compile(r"price-text--price-part")}).find_all("span")[-1].text
                    price = price.replace('\n', '').strip()
                    price_nums = ''
                    for i in filter(lambda x: x.isdigit() or x == '.', price):
                        price_nums += i
                    price = float(self.formatting_quantities(price_nums))

                    # SAVING THE DATA:
                    item = ItemLoader(Course(), response)
                    item.add_value("Course_Name", course_name)
                    item.add_value("Description", description_name)
                    item.add_value("Score", score)
                    item.add_value("Students", number_of_students)
                    item.add_value("Num_of_Ratings", number_of_ratings)
                    item.add_value("Duration_in_hrs", duration)
                    item.add_value("Price", price)

                    yield item.load_item()

                    print("#" * 60)

            print(f"¡PAGE NUMBER '{pages}' SCRAPED!")
            pages += 1
            driver.get(f"https://www.udemy.com/courses/search/?p={pages}&q=Web+Scraping&src=ukw")

        print("¡¡¡THE SCRAPING HAS FINISHED :)!!!")