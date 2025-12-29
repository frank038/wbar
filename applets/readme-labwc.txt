For the applets to appear in the desired position, copy the 
following entries in the rc.xml file and modify them as you want:

      <windowRule title="qtaudio1" serverDecoration="no">
        <skipTaskbar>yes</skipTaskbar>
        <skipWindowSwitcher>yes</skipWindowSwitcher>
        <ignoreFocusRequest>yes</ignoreFocusRequest>
        <fixedPosition>yes</fixedPosition>
        <action name="MoveTo" x="1210" y="40" />
        <action name="ToggleAlwaysOnTop"/>
      </windowRule>
      <windowRule title="qtmpris1" serverDecoration="no">
        <skipTaskbar>yes</skipTaskbar>
        <skipWindowSwitcher>yes</skipWindowSwitcher>
        <ignoreFocusRequest>yes</ignoreFocusRequest>
        <fixedPosition>yes</fixedPosition>
        <action name="MoveTo" x="1210" y="40" />
        <action name="ToggleAlwaysOnTop"/>
      </windowRule>