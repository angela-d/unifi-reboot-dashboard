#!/usr/bin/env python3
# responsive div table by alan https://codepen.io/amwill04/pen/QNPpqx
# undocumented api usage assisted by these clever fellows:
# https://ubntwiki.com/products/software/unifi-controller/api
# https://community.ui.com/questions/How-can-I-know-all-uris-and-commands-of-the-UniFi-API/163765cb-a744-489a-993b-52df015a4a4f
'''
Status board for Ubiquity access points
'''
from socket import gaierror
from bottle import route, get, redirect, template, run, static_file, request, response, error
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import json
from operator import itemgetter
import smtplib
from email.mime.text import MIMEText
import yaml
import os

conf = yaml.safe_load(open("unificonfig.yml"))

# redirect / to create ticket page; :80 does this via nginx
@route('/')
def redirect_to_dashboard():
    ''' Redirect to landing page '''
    return redirect('/dashboard')

@error(403)
def error403(error):
    ''' ip not whitelisted '''
    return "Talk to " + conf['site_admin']+ ' if you think you should have access'

@error(500)
def error500(error):
    ''' api or programming error '''
    error_msg = '500 error: API Read Timeout. Try again in 5-10 mins.'
    ninfo = '(Sometimes the API gets overrun with simultaneous activity ' \
        'from the APs feeding their data to the API.)'

    if os.uname()[1] == conf['dev_hostname']:
        error_msg = str(error)
        return template('accesspoints', aps='', err=error_msg, \
            restartpending='false', status='', email_notification='', \
            dev='y', ticket_detail='', notification_info=ninfo, \
            ticket_total='')
    else:
        return template('accesspoints', aps='', err=error_msg, \
            restartpending='false', status='', email_notification='', \
             dev='n', ticket_detail='', notification_info=ninfo, \
            ticket_total='')

@error(502)
def error502(error):
    ''' bad gateway '''
    error_msg = '502 error: '
    ninfo = str(error)
    return template('accesspoints', aps='', err=error_msg, restartpending='false', \
        status='', email_notification='', ticket_detail='', notification_info=ninfo)

# generate a form using the bottle framework
@route('/dashboard', method=['GET', 'POST'])
def authenticate_to_unifi():
    ''' authenticate to the api '''
    ninfo = ''
    login_api = 'https://' + conf['unifi']['server'] + ':' + str(conf['unifi']['port']) + '/api/login'
    headers = {"Accept": "application/json","Content-Type": "application/json"}
    api_cred = {'username': conf['unifi']['api_user'], 'password': conf['unifi']['api_pw']}
    # store a session
    with requests.Session() as session:
        validate = session.post(login_api, headers = headers, json = api_cred, \
            verify = False, timeout = 2)

        # burp all the results at once
        if conf['debug'] == '1':
            print(validate.text)

        error_msg = ''
        if validate.status_code == 200:
            # we're authenticated, list the aps & pass the session

            # get request to pull ap data
            device_api = 'https://' + conf['unifi']['server'] + ':' + str(conf['unifi']['port']) + '/api/s/' + conf['unifi']['site'] + '/stat/device/'
            jsonify = session.get(device_api, headers = headers, verify = False, timeout = 1).text
            jsonify_load = json.loads(jsonify)
            get_aps = jsonify_load['data']

            # sort by name, otherwise insertion order is default
            get_aps = sorted(get_aps, key=itemgetter('name'))

        else:
            error_msg = 'Unable to connect to the controller; it may be undergoing maintenance. Check back.'

        if os.uname()[1] == conf['dev_hostname']:
            return template('accesspoints', aps=get_aps, err=error_msg, \
                restartpending='', status='', email_notification='', \
                dev='y', ticket_detail='', notification_info=ninfo, \
                ticket_total='')
        else:
            return template('accesspoints', aps=get_aps, err=error_msg, 
            restartpending='', status='', email_notification='', \
            dev='n', ticket_detail='', notification_info=ninfo, \
            ticket_total='')


@route('/restartap', method='POST')
def collect_restart_data():
    ''' prepare pre-restart data collection '''
    subject = ''
    ticketnumber = ''
    ap = request.forms.get('ap')
    mac = request.forms.get('mac')
    devices = request.forms.get('devices')
    ticketnumber = request.forms.get('ticketnumber')
    notification = 'Restart pending for ' + ap
    restartpending = 'true'

    # prettify the device totals
    if int(devices) >= 2:
        detail = devices + ' devices will shift to nearby access points'
    elif int(devices) == 1:
        detail = devices + ' device will shift to a nearby access point'
    else:
        detail = 'no active devices to disrupt'
    ninfo = '(' + detail + ')'

    # if a ticket # is entered, see if it exists & return a bool var
    if ticketnumber:
        api = 'https://' + conf['zendesk']['domain'] + '/api/v2/tickets/' + str(ticketnumber) + '.json'
        auth = (conf['zendesk']['user'], conf['zendesk']['token'])
        zen = requests.get(api, auth=auth, timeout = 2)

        ticket = json.loads(zen.text)

        if zen.status_code == 200:
            subject = ticket['ticket']['subject']
            ticketnumber = int(ticket['ticket']['id'])
        elif zen.status_code == 404:
            subject = 'Invalid ticket'
            ticketnumber = '0'
        else:
            subject = ''
            ticketnumber = ''

    if os.uname()[1] == conf['dev_hostname']:
        return template('restartap', err=notification, \
            restartpending=restartpending, ap_to_restart=ap, \
            mac=mac, dev='y', email_notification='', \
            ticket_detail=subject, notification_info=ninfo, \
            devices=devices, ticketnumber=ticketnumber)
    else:
        return template('restartap', err=notification, \
            restartpending=restartpending, ap_to_restart=ap, \
            mac=mac, dev='n', email_notification='', \
            ticket_detail=subject, notification_info=ninfo, \
            devices=devices, ticketnumber=ticketnumber)
    


@route('/rebootinit', method='POST')
def trigger_reboot():
    ''' initialize the reboot '''
    ap = request.forms.get('ap')
    mac = request.forms.get('mac')
    ticketnumber = request.forms.get('ticketnumber')
    justtesting = request.forms.get('justtesting')
    # only process replace if username is populated
    if request.forms.get('username'):
        # remove extra @example.com if entered in the notification
        username = request.forms.get('username').replace(conf['mail']['domain'], '').strip()
        receiver = username + conf['mail']['domain']
    else:
        username = request.forms.get('username')
        receiver = ''
    restartpending = 'false'
    notification = 'Restart command submitted for ' + ap

    # webhook for diagnostics
    if justtesting != '':
        # this hasn't been built, yet
        bla = 'bla'

    # the scary bits
    login_api = 'https://' + conf['unifi']['server'] + ':' + str(conf['unifi']['port']) + '/api/login'
    headers = {"Accept": "application/json","Content-Type": "application/json"}
    api_cred = {'username': conf['unifi']['api_user'], 'password': conf['unifi']['api_pw']}

    # store a session
    with requests.Session() as session:
        validate = session.post(login_api, headers = headers, json = api_cred, verify = False, timeout = 2)

        # burp all the results at once
        if conf['debug'] == '1':
            print(validate.text)

        error_msg = ''
        if validate.status_code == 200:
            reboot_api = 'https://' + conf['unifi']['server'] + ':' + str(conf['unifi']['port']) + '/api/s/' + conf['unifi']['site'] + '/cmd/devmgr'
            headers = {"Accept": "application/json","Content-Type": "application/json"}
            reboot_params = {"mac": mac, "cmd": 'restart'}
            start_reboot = session.post(url=reboot_api, headers = headers, json = api_cred, params=reboot_params, verify = False, timeout = 3)

            # reboot (trigger) was successful; pass along the good news
            if start_reboot.status_code == 200:
                # zendesk integration
                if ticketnumber is not None and request.POST:
                    message_body = \
                        'Followup regarding your reported wifi issue for ' + ap + ' -- a remote reboot command ' \
                        'has been sent to it, which will trigger affected traffic to temporarily shift ' \
                        'to the next nearest access point.' + "\n" \
                        'You may notice the normally blue LED turn white or flash briefly ' \
                        'during the reboot process.' + "\n\n" \
                        '- Helpdesk' + "\n" \
                        'support@example.com - xxx-xxx-xxxx - https://support.example.com'

                    # send data to zendesk
                    api = 'https://' + conf['zendesk']['domain'] + '/api/v2/tickets/' + ticketnumber + '.json'
                    auth = (conf['zendesk']['user'], conf['zendesk']['token'])
                    headers = {"Accept": "application/json","Content-Type": "application/json"}
                    params= {
                        "ticket": {
                            "comment": {
                                "author_id": int(conf['zendesk']['assignee']),
                                "body": message_body, "public": True
                            },
                            "assignee_id": int(conf['zendesk']['assignee']),
                            "status": "solved"
                        }
                    }
                    params = json.dumps(params)

                    update_ticket = requests.put(api, data=params, auth=auth, \
                        headers=headers, timeout=2)

                    if update_ticket.status_code == 200:
                        status = 'Ticket # ' + ticketnumber + ' has been updated & marked solved'
                    else:
                        status = 'There was a problem updating the ticket; you may need to ' \
                            'manually inform the user you rebooted the AP & close #' + ticketnumber + update_ticket.text

                # if the username field is set, let's shoot them an email
                if receiver != '' and request.POST:
                    message_body = \
                        'Followup note from the Helpesk: ' + "\n" \
                        'Regarding your reported wifi issue for ' + ap + ' -- a remote reboot command ' \
                        'has been sent to it, which will trigger affected traffic to temporarily shift ' \
                        'to the next nearest access point.' + "\n" \
                        'You may notice the normally blue LED turn white or flash briefly ' \
                        'during the reboot process.' + "\n\n" \
                        '- Helpdesk' + "\n" \
                        'support@example.com - xxx-xxx-xxxx - https://support.example.com'

                    format_message = MIMEText(message_body)
                    format_from = str(conf['mail']['sender_name']) + ' <' + conf['mail']['sender'] + '>'
                    format_message['Subject'] = conf['email_subject'] + ap
                    format_message['From'] = format_from
                    format_message['To'] = receiver

                    try:
                        with smtplib.SMTP(conf['mail']['server'], conf['mail']['port']) as server:
                            server.set_debuglevel(1)
                            server.sendmail(receiver, receiver, format_message.as_string())
                            server.quit()

                        # tell the script to report if your message was sent or which errors need to be fixed
                        status = 'A notification was sent to ' + receiver + ' regarding their complaint being addressed'
                    except (gaierror, ConnectionRefusedError):
                        status = 'Failed to connect to the server. Bad connection settings?'
                    except smtplib.SMTPServerDisconnected:
                        status = 'Failed to connect to the mail server. Wrong user/password?'
                    except smtplib.SMTPException as error_msg:
                        status = 'Nothing has been sent: ' + str(error_msg)
            elif receiver != '' and request.POST:
                status_code = str(validate.status_code)
                notification = 'Reboot trigger was not successful:' + "\n\r" \
                    'Status code: ' + status_code  + "\n\r" \
                    'AP: ' + ap + ', MAC: ' + mac + "\n\r" \
                    'API: /api/login' + "\n\r" \
                    'Validation text:' + start_reboot.text

        if os.uname()[1] == conf['dev_hostname']:
            return template('rebootinit', banner=notification, \
                restartpending=restartpending, email_notification=status, \
                dev='y')
        else:
            return template('rebootinit', banner=notification, \
                restartpending=restartpending, email_notification=status, \
                dev='n')

@route('/inc/<filename>')
def send_css(filename):
    ''' <filename> is a wildcard, so it'll pull everything - css, images, etc.'''
    return static_file(filename, root='static/inc')

# run paste server instead of default
if os.uname()[1] == conf['dev_hostname']:
    run(server='paste', host='localhost', port=8000, debug=True, reloader=True)
else:
    run(server='paste', host='localhost', port=8000, debug=False)