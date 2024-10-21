# Selenium Automation for Google Forms
# author: @atharvnaik

import logging
import re
import time
from os import path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class ColoredFormatter(logging.Formatter):
    # ANSI escape sequences for colors
    COLOR_CODES = {
        'ERROR': '\033[91m',    # red
        'CRITICAL': '\033[91m', # red
        'WARNING': '\033[93m',  # yellow
        'DEBUG': '\033[92m',    # green
        'INFO': '\033[94m',     # blue
        'RESET': '\033[0m',     # reset to default color
    }

    def format(self, record):
        color_code = self.COLOR_CODES.get(
            record.levelname, self.COLOR_CODES['RESET'])
        message = super().format(record)
        return f"{color_code}{message}{self.COLOR_CODES['RESET']}"


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()

formatter = ColoredFormatter('%(levelname)s: %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)


class GForm:
    """
    A class to fill out Google Forms using Selenium WebDriver.
    """

    def __init__(self) -> None:
        """
        Initialize the GForm class with the Google Form URL.
        """

        options = webdriver.ChromeOptions()
        src = path.abspath(path.join(path.dirname(__file__), 'data'))
        options.add_argument(f'--user-data-dir={src}')
        # options.add_argument('--headless')
        # options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('log-level=3')
        options.add_experimental_option(
            "excludeSwitches", ['enable-automation'])
        self.driver = webdriver.Chrome(options=options)
        self.WAIT = 5

    def create_mappings(
            self,
            rawdata: dict,
            exhaustive: bool = False
    ) -> dict:
        """
        Process raw data and create form data mappings with X-paths.

        Args:
            rawdata (dict): A dictionary containing form field information.
            exhaustive (bool): Flag to search for all possible text fields. Default is False.

        Returns:
            mappings (dict): A dictionary of form data with X-paths and corresponding values.

        Example:
        ```python
        rawdata = {
            'text': {
                'Email': {
                    'types': ['text', 'email'],
                    'response': 'resp',
                },
                'Name': {
                    'types': ['text'],
                    'response': 'resp',
                }
            },
            'radio': {
                'Solvents': {
                    'choice': 'DMSO',
                    'choice_num': 6, # optional
                }
            },
            'checkbox': {
                'Experiments': {
                    'choices': ['exp-1', 'exp-2'],
                }
            },
        }

        mappings = {
            'text': {
                '<X-path for Email>': 'resp',
                '<X-path for Name>': 'resp',
            },
            'radio': [
                '<X-path for DMSO>',
            ],
            'checkbox': [
                '<X-path for exp-1>',
                '<X-path for exp-2>',
            ],
        }
        ```
        """

        mappings = {
            'text': {},         # text fields

            # choice fields
            'radio': [],        # radio fields
            'checkbox': [],     # checkbox fields

            'fallbacks': {},    # TODO: fallbacks on failure
        }

        for question, meta in rawdata['text'].items():

            if 'types' in meta.keys():
                text_types = ' or '.join(
                    [f'@type="{type_}"' for type_ in meta['types']]
                )
                mappings['text'][f'//span[contains(text(), "{question}")]/../../../..//input[{text_types}]'] = meta['response']

            if not 'textarea' in meta.keys():
                meta['textarea'] = True if exhaustive else False

            if meta['textarea'] == True:
                key, value = mappings['text'].popitem()
                mappings['text'][f'{key} | //span[contains(text(), "{question}")]/../../../..//textarea'] = value

        for question, meta in rawdata['radio'].items():
            choice = meta['choice']
            mappings['radio'].append(
                f'//span[contains(text(), "{choice}")]/../../../../..//label'
            )

        for question, meta in rawdata['checkbox'].items():
            for choice in meta['choices']:
                mappings['checkbox'].append(
                    f'//span[contains(text(), "{choice}")]/../../../../..//label'
                )

        self.mappings = mappings
        self.url = rawdata.get('url', None)
        return self.mappings

    def fill(
            self,
            url: str = None,
            submit=True,
            interactive=False,
            review_before_submit=False,
            clear=False
    ) -> None:
        """
        Fill out the Google Form using the form data mappings and submit the form.

        Args:
            url (str): The URL of the Google Form to be filled. Automatically set from rawdata if provided. Default is None.
            submit (bool): Submit the form after filling. Default is True.
            interactive (bool): Interactive mode. Prompts user input before proceeding. Default is False.
            review_before_submit (bool): Review the form before submitting. Default is False.
            clear (bool): Clears the form before filling. Default is False. (Experimental)

        Returns:
            t (float): Time taken to fill the form.

        Example:
        ```python
        gform.fill(submit=True, interactive=True, review_before_submit=True, clear=False)
        ```
        """

        self.url = url if url else self.url
        assert self.url, logger.fatal("URL not provided")
        assert re.match(r'^https://.*$', self.url), logger.fatal("Invalid URL")
        t = -1
        cancel = False
        try:
            self.driver.get(self.url)
            if not interactive:
                time.sleep(.5)
            cancel = input(
                "Press <Enter> to start filling or q to quit >> ") == 'q' if interactive else False
            if cancel:
                return t

            start = time.time()

            # handle clearing
            if clear:
                clear_button = WebDriverWait(self.driver, self.WAIT).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//span[text()="Clear form"]'))
                )
                clear_button.click()

            # text fields
            for input_locator, value in self.mappings['text'].items():
                try:
                    input_field = WebDriverWait(self.driver, self.WAIT).until(
                        EC.element_to_be_clickable((By.XPATH, input_locator))
                    )
                    input_field.clear()
                    input_field.send_keys(value)
                    assert input_field.get_attribute(
                        'value') == value, f"Value mismatch: {input_field.get_attribute('value')} != {value}"
                except Exception as e:
                    logger.warning(
                        f"Could not fill at location: {input_locator}")
                    continue

            # choice fields - radio
            for input_locator in self.mappings['radio']:
                try:
                    input_field = WebDriverWait(self.driver, self.WAIT).until(
                        EC.element_to_be_clickable((By.XPATH, input_locator))
                    )
                    if not input_field.is_selected():
                        input_field.click()
                except Exception as e:
                    logger.warning(
                        f"Could not fill at location: {input_locator}")
                    continue

            # choice fields - checkbox
            for input_locator in self.mappings['checkbox']:
                try:
                    input_field = WebDriverWait(self.driver, self.WAIT).until(
                        EC.element_to_be_clickable((By.XPATH, input_locator))
                    )
                    fr = input_field.get_attribute('for')
                    aria_checked = self.driver.find_element(
                        By.ID, fr).get_attribute('aria-checked')
                    if aria_checked == 'false':
                        input_field.click()
                except Exception as e:
                    logger.warning(
                        f"Could not fill at location: {input_locator}")
                    continue

            # TODO: fallbacks

            # handle submit
            if submit:
                if review_before_submit and interactive:
                    cancel = input(
                        "Review the form and press <Enter> to submit or 'q' to cancel") == 'q'
                if not cancel:
                    submit_button = WebDriverWait(self.driver, self.WAIT).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, '//span[text()="Submit"]'))
                    )
                    submit_button.click()
            t = time.time() - start
            input("Press <Enter> to close the browser") if interactive else None

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
        finally:
            self.driver.quit()
            return t
