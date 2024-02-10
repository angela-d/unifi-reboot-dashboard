<!DOCTYPE html>
  <head>
    <title>Initializing Reboot - Wifi Dashboard/title>
    <link rel="stylesheet" href="/inc/form_styles.css">
    <link rel="icon" type="image/png" href="inc/wifi.svg">
  </head>
<body>
  <div class="background-image"></div>
  <div class="wrapper">
      <div id="one"><a href="/"><img src="/inc/wifi.png alt="wifi" style="max-width:37%;"></a></div>
      <div id="two">Wifi Dashboard</div>
  </div>
  <div id="ticket_form">
  % if dev == 'y':
  <div class="box">
    <div class="ribbon"><span>dev</span></div>
  </div>
  % end
  % if banner:
    <div class="notice">{{banner}}
      <div class="nousers">It will disappear from the dashboard temporarily</div>
    </div>
  % end
  % if email_notification is not '':
    <div class="notice">{{email_notification}}</div>
  % end
  % if restartpending is 'false':
    <div class="overlay">
      <a href="/">Refresh dashboard</a>
    </div>
  % end
  </div>
</div>
</body>
</html>
