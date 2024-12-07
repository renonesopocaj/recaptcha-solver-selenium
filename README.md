# recaptcha-v2-solver-selenium
A recaptcha (v2) solver in python using selenium and undetectable chromedriver, able to return the solved captcha token by using the audio mode.
You can use it in two ways:
- just use the `captcha_solver` function to solve the captcha in your target site and then submit it.
- By using function `captcha2token` to return the token of the solved captcha, you can possibly run it in parallel with your main code, and you can give your main code the returned token that you will insert to validate the captcha on your main code by using (for example) `document.getElementById('g-recaptcha-response').value = '{token}';`. This lets you avoid having to wait for the whole captcha being solved on your main code. The code also contains experimental function `send_token` to try inserting the token in the page, after solving the captcha (though it is not the purpose of the code).
Note that the token expires after 2 minutes.

The code already changes user agent, and, by using selenium or selenium-wire appropriate options, you can use proxies to further avoid being detected.
If "AutomatedQueriesException" appears, you will probably have to change IP or user agent.
The code already solves captchas even if the more than one prompt is required.
## Getting started
You have to install the following libraries: `selenium`, `undetectable-chromedriver`, `pydub`, `speech_recognition`, `pocketsphinx` by using command:
`pip install <library>`
and you might have to run the following commands in the cmd:
`pip install blinker==1.7.0`
`pip install setuptools`
## Usage
Insert the page which contains the captcha by using user input, or otherwise type 'demo' to see the code in action on a demo page.
## Demo
Note that there is also the `send_token` function that inserts the token after reloading the page (as you can see by the green tick after the reload of the page, which tells us that the captcha has been recognized as solved/correct even without having to actually solve it again).

https://github.com/user-attachments/assets/99465ab5-4756-4de6-a1ab-a0b9d7900a02

