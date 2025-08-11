# ti-84-netinteraction
An amalgamation of resources to transmit data between two TI-84 calculators wirelessly, complete with authentication and sending/receiving messages.

(Note, this will take use of your string variables, so make sure nothing important is being used on there!)

## HOW TO USE

### ON YOUR HOME COMPUTER:

1. Download the latest release

2. Make sure you have python installed on your home computer in addition to PIP (to get requests & tivars libraries), or have a portable version of both 

3. Use software similar or exactly like TI Connect CE to transmit all .8xp and .8xg files to the calculator using the USB-A to USB-B port, and save it in the archive. This does require administrative access, but it is one-time only. You can use a standard account for the following steps.

4. Modify the messenger.py script to use a custom server, or leave it as is to use the automatic server. If running locally, change the server to localhost.

5. Run the messenger.py script

### ON YOUR CALCULATOR

#### TO AUTHENTICATE

1. Open up prgmAUTH

2. Set up your account by selecting 'sign up'. If you already made an account with the same name, choose 'log in' instead.

3. Set up your username and password

4. Once that's completed, select prgmTRANSFER and wait until the messenger.py script confirms that the data has been sent, or wait for 'event completed' return on the calculator

#### TO SEND MESSAGES

1. Open up prgmSENDMSG

2. Type in the other person's username to which you want to send message sto

3. Type in the message

4. Open up prgmTRANSFER and wait until the messenger.py script confirms that data has been sent, or wait for 'event completed' return on the calculator

#### TO RECEIVE MESSAGES

1. Open up prgmTRANSFER to pre-emptively receive any messages sent your way, and wait until the messenger.py script confirms that data has been sent, or wait for 'event completed' return on the calculator

2. Open up prgmGETMSG

3. Press enter to get new messages

#### TO USE AI:

1. Open up prgmHELP and insert your question

2. Open up prgmTRANSFER to transmit the request and get back data

3. Choose the receive mode on the program to receive the AI response

## NOTES:

This must be plugged into your laptop or computer at all times to receive/authenticate/send messages

This can work with any TI-84 and further calculators which have USB functionality

You can run a server locally or elsewhere, but you'll have to change the messenger server variable in messenger.py

Again, make sure you have python installed wirelessly using something like WinPython or Portable Python and pip installed on there as well to download requests & tivars
   
