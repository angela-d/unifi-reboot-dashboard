<!DOCTYPE html>
  <head>
    <title>Access Points - Wifi Dashboard</title>
    <link rel="stylesheet" href="/inc/form_styles.css">
    <link rel="icon" type="image/png" href="inc/wifi.svg">
  </head>
<body>
  <div class="background-image"></div>
  <div class="wrapper">
      <div id="one"><a href="/"><img src="/inc/wifi.png" alt="wifi"></a></div>
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
    % if ticket_total is not '' and ticket_total == 1:
      <div class="notice">Located ticket #{{ticketnumber}}; {{ticket_detail}}
        <div class="up">It will be updated & closed after you press the reboot button!</div>
      </div>
    % end

<div class="overlay">
  % if err is '':
  <div class="table" id="results">
    <div class="theader">
      <div class="table_header">Access Point</div>
      <div class="table_header">Option</div>
    </div>
    % if aps:
    % for ap in aps:
    % if 'is_access_point' in ap:
    % if ap['is_access_point']:

    <div class="table_row">
      <div class="table_small">
        <div class="table_cell">AP</div>
        <div class="table_cell"><img style="float: left;margin:auto;" src="inc/ap.png" title="{{ap['name']}} ufo">{{ap['name']}}</div>
          % if ap['satisfaction'] >= 94:
          <div class="up">Experience: {{ap['satisfaction']}}%</div>
          % elif ap['satisfaction'] == -1:
          <div class="nousers">-</div>
          % elif ap['satisfaction'] <= 80 <= 93:
          <div class="maint">Possible issues: {{ap['satisfaction']}}% experience</div>
          % elif ap['satisfaction'] <= 0 <= 79:
          <div class="down">Poor Experience: {{ap['satisfaction']}}%</div>
          % else:
          <div class="nousers">Experience: {{ap['satisfaction']}}%</div>
          % end
      </div>
      <div class="table_small">
        <div class="table_cell">Option</div>
        <div class="table_cell">
          <form action="/restartap" method="post">
            <input name="ap" type="hidden" value="{{ap['name']}}" />
            <input name="mac" type="hidden" value="{{ap['mac']}}" />
            <input name="devices" type="hidden" value="{{ap['num_sta']}}" />
            <input type="submit" value="Restart {{ap['name']}}" />
            % if ap['num_sta'] >= 2 or ap['num_sta'] == 0:
            <div class="apstats">{{ap['num_sta']}} devices</div>
            % else:
            <div class="apstats">{{ap['num_sta']}} device</div>
            % end
          </form>
        </div>
      </div>
      </div>
      % end
    % end
    % end
    % end
  </div>
</div>
</div>
</body>
</html>
