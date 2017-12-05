Given an Archivematica instance
  When the user goes to Administration tab
  And the user goes to Version
  Then Version is <X.X.X>
  And a privileged user runs the command "yum update -y"
  And reboots
  When the user goes to Administration tab
  And the user goes to Version
  Then Version is <X.Y.Z>
