########################################################################################################################
#                                                         IMPORT                                                       #
########################################################################################################################

import os
import requests
import time

import pydub
from pydub import AudioSegment
import speech_recognition as sr

import selenium
from selenium.webdriver.common.keys import Keys
import selenium.common.exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import undetected_chromedriver as uc

import json
from fake_useragent import UserAgent

AudioSegment.converter = "C:\\ffmpeg-2024-11-11-git-96d45c3b21-full_build\\bin\\ffmpeg.exe"
AudioSegment.ffmpeg = "C:\\ffmpeg-2024-11-11-git-96d45c3b21-full_build\\bin\\ffmpeg.exe"
AudioSegment.ffprobe ="C:\\ffmpeg-2024-11-11-git-96d45c3b21-full_build\\bin\\ffprobe.exe"

########################################################################################################################
#                                              FRAME SEARCHING                                                         #
########################################################################################################################

class UnableToSendTokenException(Exception):
    pass

class NoRecaptchaFrameException(Exception):
    pass

class NoRecaptchaChallengeFrameException(Exception):
    pass

class UnknowFrameTitleException(Exception):
    pass

def get_frame_titles(driver):
    frame_list = driver.find_elements(By.TAG_NAME, 'iframe')
    frame_titles_list = []
    for frame in frame_list:
        frame_title = frame.get_attribute('title')
        frame_titles_list.append(frame_title)
    if len(frame_titles_list) != len(frame_list):
        raise UnknowFrameTitleException
    return [frame_list, frame_titles_list]

def get_reCAPTCHA_frame(frame_titles_list, frame_list):
    # This function searches for the "reCAPTCHA" frame
    reCAPTCHA_frame = None
    for i in range(0, len(frame_titles_list)):
        if frame_titles_list[i] == 'reCAPTCHA':
            reCAPTCHA_frame = frame_list[i]
            return reCAPTCHA_frame
    return reCAPTCHA_frame

def get_recaptchachallenge_frame(frame_titles_list, frame_list):
    # this function searches for the frame named "recaptcha challenge expires in two minutes"
    recaptchachallenge_frame = None
    for i in range(0, len(frame_titles_list)):
        if frame_titles_list[i] == 'recaptcha challenge expires in two minutes':
            recaptchachallenge_frame = frame_list[i]
            return recaptchachallenge_frame
    return recaptchachallenge_frame

def switch_to_recaptcha_frame(driver):
    # This function switches to the frame with title "reCAPTCHA"
    driver.switch_to.default_content()
    timeout = time.perf_counter() + 20
    reCAPTCHA_frame = None
    while (reCAPTCHA_frame == None and time.perf_counter() < timeout):
        frame_titles_list = get_frame_titles(driver)[1]
        frame_list = get_frame_titles(driver)[0]
        reCAPTCHA_frame = get_reCAPTCHA_frame(frame_titles_list, frame_list)
    if (time.perf_counter() > timeout):
        raise NoRecaptchaFrameException("Cannot find recaptcha frame")
    driver.switch_to.frame(reCAPTCHA_frame)

def switch_to_recaptchachallenge_frame(driver):
    # This function switches to the frame named "recaptcha challenge expires in two minutes"
    driver.switch_to.default_content()
    timeout = time.perf_counter() + 20
    recaptchachallenge_frame = None
    while (recaptchachallenge_frame == None and time.perf_counter() < timeout):
        frame_titles_list = get_frame_titles(driver)[1]
        frame_list = get_frame_titles(driver)[0]
        recaptchachallenge_frame = get_recaptchachallenge_frame(frame_titles_list, frame_list)
    if (time.perf_counter() > timeout):
        raise NoRecaptchaChallengeFrameException("Cannot find recaptcha-challenge frame")
    driver.switch_to.frame(recaptchachallenge_frame)

########################################################################################################################
#                                         AUTOMATEDQUERIES EXCEPTION PART                                              #
########################################################################################################################

class AutomatedQueriesException(Exception):
    pass

def detect_automatedqueries(driver):
    """This function detects if there is the text "Your computer or network may be sending automated queries [...]"
    on the captcha, which requires being able to change all the necessary parameters (for example IP)"""
    try:
        switch_to_recaptchachallenge_frame(driver=driver)
        xpath_automatedqueries = '/html/body/div/div/div[1]/div[2]/div'
        text_automatedqueries = driver.find_element(By.XPATH, xpath_automatedqueries).text
        if text_automatedqueries == '''Your computer or network may be sending automated queries. To protect our users, we can't process your request right now. For more details visit our help page.''':
            raise AutomatedQueriesException('''There is the "Your computer or network may be sending automated queries [...]" text on the captcha, whic isn't letting the program solve captchas. Try changing user agent, proxy or wait some time\n''')
    except (selenium.common.exceptions.NoSuchElementException, selenium.common.exceptions.ElementNotSelectableException,
            selenium.common.exceptions.ElementNotVisibleException,
            selenium.common.exceptions.ElementNotInteractableException,
            selenium.common.exceptions.ElementClickInterceptedException,
            selenium.common.exceptions.TimeoutException):
        pass

########################################################################################################################
#                                         VARIOUS EXCEPTIONS                                                           #
########################################################################################################################

class AttributeOfDisabledParameterError(Exception): # eccezione un problema legato a resolve captcha
    pass

class FrameNotFoundException(Exception):
    pass

########################################################################################################################
#                                             SOLVE                                                                    #
########################################################################################################################

class UnableDetectLanguageException(Exception):
    pass

class CannotFoundAudioSourceException(Exception):
    pass

class FFmpegException(Exception):
    pass

def detect_language(driver):
    """Tries to detect the language of the browser"""
    driver.switch_to.default_content()
    try:
        switch_to_recaptcha_frame(driver=driver)
        html_elements = driver.find_elements(By.TAG_NAME, 'html')
        language = html_elements[0].get_attribute('lang')
        return language
    except:
        raise UnableDetectLanguageException

def obtain_source(driver):
    """Obtains the source of the audio captcha, to download it and then render it"""
    timeout = time.perf_counter() + 10
    while (time.perf_counter() < timeout):
        try:
            detect_automatedqueries(driver=driver)
            switch_to_recaptchachallenge_frame(driver=driver)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "audio-source")))
            source_link = driver.find_element(By.ID, "audio-source").get_attribute("src")
            return source_link
        except AutomatedQueriesException:
            raise AutomatedQueriesException('''There is the "Your computer or network may be sending automated queries [...]" text on the captcha, which isn't letting the program solve captchas. We suggest you try changing user agent, proxy or wait some time\n''')
        except selenium.common.exceptions.NoSuchElementException:
            raise selenium.common.exceptions.NoSuchElementException
        except selenium.common.exceptions.TimeoutException:
            detect_automatedqueries(driver=driver)
    if (time.perf_counter() > timeout):
        raise CannotFoundAudioSourceException

########################################################################################################################
#                                             SOLVES CAPTCHA                                                           #
########################################################################################################################

class HTTPErrorException(Exception):
    pass

class RequestDownloadException(Exception):
    pass

class AudioRecognitionException(Exception):
    pass

class AudioResponseException(Exception):
    pass

class WrongUrlException(Exception):
    pass

class SolverTimeoutException(Exception):
    pass

def go_2_AudioMode(driver):
    """This function switches the captcha to audiomode"""
    detect_automatedqueries(driver=driver)
    switch_to_recaptcha_frame(driver=driver)
    # click to open the challenge
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "recaptcha-checkbox-border")))
    driver.find_element(By.CLASS_NAME, "recaptcha-checkbox-border").click()
    switch_to_recaptcha_frame(driver=driver)
    detect_automatedqueries(driver=driver)
    switch_to_recaptchachallenge_frame(driver=driver)
    # switch to audio mode: if the element is not clickable, then it means that the captcha has automaticlaly been solved
    try:
        id_audio = 'recaptcha-audio-button'
        xpath_audio = '//*[@id="recaptcha-audio-button"]'
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, id_audio)))
        driver.find_element(By.XPATH, xpath_audio).click()
        return False
    except selenium.common.exceptions.ElementNotInteractableException:
        return True
    except selenium.common.exceptions.ElementClickInterceptedException:
        return True

def retrieve_audiofile(driver, counter):
    """This function obtaines the source link and downloads the .mp3 audiofile"""
    timeout = time.perf_counter() + 200
    while time.perf_counter() < timeout:
        src = obtain_source(driver=driver)
        try:
            session = requests.Session()
            r = session.get(src, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36', 'accept':
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'sec-ch-ua' : '''"Chromium";v="93", " Not A;Brand";v="99", "Google Chrome";v="93"''', 'sec-fetch-dest' :
                'document'})
            with open(os.path.normpath(os.getcwd() + "\\sample{}.mp3".format(counter)), 'wb') as f:
                f.write(r.content)
            break
        except requests.exceptions.HTTPError: # sometimes the link of the source doesn't work, so you have to reload the captcha
            if r.status_code == 404:
                detect_automatedqueries(driver=driver)
                switch_to_recaptchachallenge_frame(driver=driver)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "recaptcha-reload-button")))
                driver.find_element(By.ID, "recaptcha-reload-button").click()
                continue
            else:
                raise HTTPErrorException
        except AutomatedQueriesException:
            raise AutomatedQueriesException('''There is the "Your computer or network may be sending automated queries [...]" text on the captcha, which isn't letting the program solve captchas. We suggest you try changing user agent, proxy or wait some time\n''')
        except:
            raise RequestDownloadException
    if (time.perf_counter() > timeout):
        raise SolverTimeoutException

def audioSource2text(driver, counter):
    """This function retrieves the audio file from the audio source and process it"""
    timeout = time.perf_counter() + 200
    while time.perf_counter() < timeout:
        retrieve_audiofile(driver=driver, counter=counter)
        try:
            sound = pydub.AudioSegment.from_mp3(os.path.normpath(os.getcwd() + "\\sample{}.mp3".format(counter)))
            sound.export(os.path.normpath(os.getcwd() + "\\sample{}.wav".format(counter)), format="wav")
            sample_audio = sr.AudioFile(os.path.normpath(os.getcwd() + "\\sample{}.wav".format(counter)))
        except:
            raise FFmpegException
        r = sr.Recognizer()
        with sample_audio as source:
            audio = r.record(source)
        try:
            key = r.recognize_sphinx(audio)
        except sr.UnknownValueError: # the audiofile is too noisy: you have to load a new captcha
            try:
                detect_automatedqueries(driver)
                switch_to_recaptchachallenge_frame(driver)
                driver.find_element(By.ID, "recaptcha-reload-button").click()
            except AutomatedQueriesException:
                raise AutomatedQueriesException('''There is the "Your computer or network may be sending automated queries [...]" text on the captcha, which isn't letting the program solve captchas. We suggest you try changing user agent, proxy or wait some time\n''')
            continue
        except AutomatedQueriesException:
            raise AutomatedQueriesException('''There is the "Your computer or network may be sending automated queries [...]" text on the captcha, which isn't letting the program solve captchas. We suggest you try changing user agent, proxy or wait some time\n''')
        except: #print(newErrorAudioRecognition_art, '\n', sys.exc_info()[0])
            raise AudioRecognitionException
        break
    if (time.perf_counter() > timeout):
        raise SolverTimeoutException
    return key

def resolve_captcha(driver, counter):
    """This function solves the captcha and submits it"""
    timeout = time.perf_counter() + 200
    while time.perf_counter() < timeout:
        key = audioSource2text(driver=driver, counter=counter)
        detect_automatedqueries(driver=driver)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "audio-response")))
        driver.find_element(By.ID, "audio-response").send_keys(key.lower())
        driver.find_element(By.ID, "audio-response").send_keys(Keys.ENTER)
        try: # i have to search an error text that requires a different case if there is or if there is not
            detect_automatedqueries(driver=driver)
            switch_to_recaptchachallenge_frame(driver=driver)
            WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located((By.CLASS_NAME, "rc-audiochallenge-error-message")))
            error = driver.find_element(By.CLASS_NAME, "rc-audiochallenge-error-message").text
            text = 'Multiple correct solutions required - please solve more.'
            if error == text: # (1) case: I have a text, that can appear both if the captcha is solved and if it's not solved, and
                # we must discriminate those situations
                try:
                    detect_automatedqueries(driver=driver)
                    switch_to_recaptchachallenge_frame(driver=driver)
                    WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#audio-response')))
                    time.sleep(3)
                    response_field = driver.find_element(By.CSS_SELECTOR, '#audio-response')
                    # this field lets us discriminate between the case where there's the captcha and it's resolved (1.1) or not (1.2) or the bug isn't solved by this code (1.3)
                    disabled = response_field.get_attribute('disabled')
                    if disabled == 'true': #(1.1)
                        break
                    elif disabled == '': #(1.1)
                        break
                    elif disabled == 'false': #(1.2)
                        continue
                    elif disabled == None: #(1.2)
                        continue
                    else:
                        raise AttributeOfDisabledParameterError('''Il parametro 'disabled' ha un attributo imprevisto''')
                except AutomatedQueriesException:
                    raise AutomatedQueriesException('''There is the "Your computer or network may be sending automated queries [...]" text on the captcha, which isn't letting the program solve captchas. We suggest you try changing user agent, proxy or wait some time\n''')
                except selenium.common.exceptions.NoSuchAttributeException: #(1.2)
                    continue
                except: # (1.3)
                    raise AudioResponseException
            else: # since I don't have the error text, the captcha must be solved
                break
        except (selenium.common.exceptions.NoSuchElementException, selenium.common.exceptions.ElementNotVisibleException,
                selenium.common.exceptions.ElementNotSelectableException,
                selenium.common.exceptions.ElementNotInteractableException,
                selenium.common.exceptions.TimeoutException): #(2)
            # (2) I must understand if I didn't find the error text because I have solved the captcha (2.1) or because it's hidden (2.2) or other (2.3)
            try:
                detect_automatedqueries(driver=driver)
                WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#audio-response')))
                response_field = driver.find_element(By.CSS_SELECTOR, '#audio-response')
                disabled = response_field.get_attribute('disabled')
                if disabled == 'true': #(2.1) solved
                    break
                elif disabled == '': #(2.1) solved
                    break
                elif disabled == None:  # (2.2) not solved
                    continue
                elif disabled == 'false': #(2.2) not solved
                    continue
                else:
                    raise AttributeOfDisabledParameterError('''Il parametro 'disabled' ha un attributo imprevisto''')
            except selenium.common.exceptions.NoSuchAttributeException:
                continue
            except AutomatedQueriesException:
                raise AutomatedQueriesException('''There is the "Your computer or network may be sending automated queries [...]" text on the captcha, which isn't letting the program solve captchas. We suggest you try changing user agent, proxy or wait some time\n''')
            except:
                raise AudioResponseException
        except AutomatedQueriesException:
            raise AutomatedQueriesException('''There is the "Your computer or network may be sending automated queries [...]" text on the captcha, which isn't letting the program solve captchas. We suggest you try changing user agent, proxy or wait some time\n''')
        except: # (2.3)
            raise
    if time.perf_counter() > timeout:
        raise SolverTimeoutException

def captcha_solver(driver, counter, link):
    """Tries to solve the captcha in the linked page"""
    driver.get(link)
    solved = go_2_AudioMode(driver=driver)
    if solved == False:
        resolve_captcha(driver=driver, counter=counter)
    else:
        pass

########################################################################################################################
#                                                 GET TOKEN                                                            #
########################################################################################################################

def processLog_old(driver, log, sitekey):
    """Takes the single log and goes to the message where we can get the token"""
    log = json.loads(log["message"])["message"]
    if ("Network.responseReceived" in log["method"] and "params" in log.keys()):
        try: # nel log, ottieni il parametro url
            url = ((log.get('params')).get('response')).get('url')
            if url == f"https://www.google.com/recaptcha/api2/userverify?k={sitekey}":
                body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': log["params"]["requestId"]})
                return body
            else: # not the log I want
                pass
        except AttributeError: # not the log I want
            pass

def get_token_old(driver, sitekey):
    """Hets the captcha token from the logs. It doesn't work everywhere, thus it's not used"""
    time.sleep(3)
    logs = driver.get_log("performance")
    responses = [processLog_old(driver=driver, log=log, sitekey=sitekey) for log in logs]
    responsetoken = []
    for response in responses:
        if response != None:
            responsetoken.append(response)
    try:
        token = responsetoken[0]
    except IndexError:
        raise
    gcaptcharesponse = token.get('body')
    gcaptcharesponse = gcaptcharesponse[16:]
    deletethischaracter = '''"'''
    char_index = 0
    while char_index < len(gcaptcharesponse):
        if gcaptcharesponse[char_index] == deletethischaracter:
            deletefromthischaracter_index = char_index
            break
        char_index = char_index + 1
    captcha_token = gcaptcharesponse[:deletefromthischaracter_index]
    return captcha_token

def captcha2token(driver, counter, link):
    """From the input link, solves the captcha and gets the token"""
    captcha_solver(driver=driver, counter=counter, link=link)
    timeout = time.perf_counter() + 100
    while time.perf_counter() < timeout:
        try:
            token = driver.find_element(By.ID, "recaptcha-token").get_attribute("value")
            break
        except Exception as e:
            print(f"Exception is {e}")
    if (time.perf_counter() > timeout):
        print("Unable to get token")
    print("Token:\n", token)
    return token

########################################################################################################################
#                                                SEND TOKEN                                                            #
########################################################################################################################

def refresh_and_check_loaded(driver):
    """Refreshes the page and waits until it is fully loaded"""
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'html')))
    old_page = driver.find_element(By.TAG_NAME, 'html')
    driver.refresh()
    driver.switch_to.default_content()
    new_page = driver.find_element(By.TAG_NAME, 'html')
    timeout = time.perf_counter() + 100
    while time.perf_counter() < timeout:
        if new_page.id != old_page.id:
            break
        else:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'html')))
            new_page = driver.find_element(By.TAG_NAME, 'html')
            continue
    if (time.perf_counter() > timeout):
        raise SolverTimeoutException

def send_token_naive(driver, token):
    """Sends token to the page, only trying once"""
    driver.switch_to.default_content()
    time.sleep(5)  # wait some time: deleting this might result in the js script not working properly
    script = f"""
        document.getElementById('g-recaptcha-response').value = '{token}';
    """
    driver.execute_script(script)
    time.sleep(5) # wait more: deleting this might result in the js script not working properly

def send_token(driver, token):
    """Testing function to send token to the page, with a little bit of exceptions handling"""
    try:
        time.sleep(5)
        refresh_and_check_loaded(driver)
        send_token_naive(driver, token)
        solved = go_2_AudioMode(driver=driver)
        if solved == False:
            refresh_and_check_loaded(driver)
            send_token_naive(driver, token)
            solved = go_2_AudioMode(driver=driver)
            if solved == False:
                raise UnableToSendTokenException("Unable to send the token to the page")
    except UnableToSendTokenException:
        pass
    except selenium.common.exceptions.JavascriptException:
        try:
            script = f"""
                // Check if element exists first
                var response = document.getElementById('g-recaptcha-response');
                if (!response) {{
                    // If it doesn't exist, create it
                    response = document.createElement('textarea');
                    response.id = 'g-recaptcha-response';
                    response.name = 'g-recaptcha-response';
                    response.style.display = 'none';
                    document.body.appendChild(response);
                }}
                // Now set the value
                response.value = '{token}';
            """
            driver.execute_script(script)
        except:
            pass

########################################################################################################################
#                                                MAIN                                                                  #
########################################################################################################################

if __name__ == "__main__":
    try:
        # setting up the chromedriver
        ua = UserAgent()
        userAgent = ua.random
        print(f"current user agent is {userAgent}")
        options = uc.ChromeOptions()
        options.add_experimental_option(name='prefs', value={'intl.accept_languages': 'en,en_US'})
        options.add_argument(f'user-agent={userAgent}')
        options.set_capability(name='goog:loggingPrefs', value={'performance': 'ALL'})
        driver = uc.Chrome(options=options)
        # get the input from the user. The validty of the link isn't currently checked
        link = input("please insert a valid link, or type 'demo' to test the program:\n")
        if link == 'demo':
            link = "https://www.google.com/recaptcha/api2/demo"
        # tries to solve the captcha
        token = captcha2token(driver=driver, counter=1, link=link)
        time.sleep(5)
        # tries to submit the token, even though it's not the main purpose of the program, so this is only a testing function
        send_token(driver=driver, token=token)
    finally:
        driver.quit()