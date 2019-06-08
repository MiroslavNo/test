import traderFunctions
import sys

subject = 'FATAL - 03_RESTARTtradeRunner did not work'

if(len(sys.argv) > 1):
	if (str(sys.argv[1]) == '1'):
		msg = "the runner could not be restarted - after the kill operation there was still a live python thread on the windows tasklist"
		traderFunctions.send_email(subject, msg)
	elif (str(sys.argv[1]) == '2'):
		msg = "the runner could not be restarted - after the start command no python thread was found in the windows tasklist"
		traderFunctions.send_email(subject, msg)
	else:
		subject = "ERROR in the script 09_sendEmailThatRestartFailed.py"
		msg = "The script 09_sendEmailThatRestartFailed.py was called, but no valid parameter was submitted. The script expects either a 1 (for the case where python threads could not be killed) or a 2 (for the case that the runner was called but not python thread found in the windows tasklist). The parameter which was submitted is:{}".format(str(sys.argv[1]))
		traderFunctions.send_email(subject, msg)
else:
	subject = "ERROR in the script 09_sendEmailThatRestartFailed.py"
	msg = "The script 09_sendEmailThatRestartFailed.py was called, but None parameter was submitted. The script expects either a 1 (for the case where python threads could not be killed) or a 2 (for the case that the runner was called but not python thread found in the windows tasklist)."
	traderFunctions.send_email(subject, msg)