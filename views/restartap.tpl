<!DOCTYPE html>
  <head>
    <title>Restart an AP - Wifi Dashboard</title>
    <link rel="stylesheet" href="/inc/form_styles.css">
    <link rel="icon" type="image/png" href="inc/wifi.svg">
  </head>
<body>
  <div class="background-image"></div>
  <div class="wrapper">
      <div id="one"><a href="/"><img src="/inc/wifi.png" alt="wifi" style="max-width:37%;"></a></div>
      <div id="two">Wifi Dashboard</div>
  </div>
  <div id="ticket_form">
  % if dev == 'y':
  <div class="box">
    <div class="ribbon"><span>dev</span></div>
  </div>
  % end
    % if err:
      <div class="notice">{{err}}
        <div class="nousers">{{notification_info}}</div>
      </div>
    % end
    % if email_notification is not '':
      <div class="notice">{{email_notification}}</div>
    % end
    % if ticket_detail != 'Invalid ticket' and ticketnumber:
      <div class="notice">Located ticket #{{ticketnumber}}; {{ticket_detail}}
        <div class="up">It will be updated & closed after you press the reboot button!</div>
      </div>
    % elif ticket_detail == 'Invalid ticket':
    <div class="notice">
      Ticket not found
      <div class="down">It either doesn't exist, or is not Open/Pending status</div>
    </div>
    % end

<div class="overlay">
  % if restartpending is 'true':
  Existing tickets will be auto-solved with a synopsis of work performed.<br />
  If no ticket, enter their company username and an email will be sent informing their complaint has been addressed.<br />
  At least <b>one</b> field must be filled (not both) in order to complete the reboot!
  <ul>
     % if ticketnumber is None or ticket_detail == 'Invalid ticket':
      <form action="/restartap" method="post">
        Ticket #:
        <input name="devices" type="hidden" value="{{devices}}" />
        <input name="ap" type="hidden" value="{{ap_to_restart}}" />
        <input name="mac" type="hidden" value="{{mac}}" />
        <input id="ticketnumber" class="notifyoption" type="text" placeholder="1234567890" name="ticketnumber" class="field">
        <input id="lookup" type="submit" value="Lookup Ticket"/>
        <br />
        <p></p>
      </form>
      % end
      <form action="/rebootinit" method="post">
      % if ticketnumber and ticket_detail != 'Invalid ticket':
        <input id="ticketnumber" class="notifyoption" type="text" value="{{ticketnumber}}" name="ticketnumber" class="field" readonly>
        <div class="up">Ticket located</div>
      % else :
        Reporting User's username:
        <input class="notifyoption" type="text" placeholder="firstnamelastname" name="username" class="field"><br />
        <small>Leave blank if there's an existing ticket</small>
      % end
      <p>
      <input type="checkbox" value ="justtesting" /> This is a test reboot (no diagnostics will be sent)<br />
      <input name="ap" type="hidden" value="{{ap_to_restart}}" />
      <input name="mac" type="hidden" value="{{mac}}" />
      <input type="submit" value="Restart {{ap_to_restart}} Now"/>
    </form>
    </p>
  </ul>
  % end
  </div>
</div>
</body>
</html>
