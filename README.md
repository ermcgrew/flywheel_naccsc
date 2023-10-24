# flywheel_naccsc

This script runs weekly via cron job set up by Emily on bscsub cluster. 
It checks that new flywheel session names have the correct format and fixes them, if enough information is present. 
Log is emailed to Emily, who manually fixes any sessions with unknown information.

Fuctions:
- main()
  - check_correct(sessionlabellist, subject, date)
  - rename_session(session, subject, date)
  - add_session_tag(session, study)
- email_log(logfilepath)
- parse_log(logfilepath,logdir)

Log levels
- Debug: correct session label
- Info: renamed session label
- Warning: incorrectly formatted subject label OR insufficient information for full renaming

detailed logs of each weekly run are saved at 
/project/wolk/Prisma3T/relong/naccsc_fw_session_rename_logs/log_check_new_session_names_{datetime}.txt
- get list of renamed sessions with: `cat log_check_new_session_names_{datetime}.txt | grep INFO | cut -d ":" -f 3,4`  
- get list of items needing attention with: `cat log_check_new_session_names_{datetime}.txt | grep WARNING`

log of all session names changed by this script, in the format old name:new name:date changed, are saved at 
/project/wolk/Prisma3T/relong/naccsc_fw_session_rename_logs/all_fw_session_renames.txt
