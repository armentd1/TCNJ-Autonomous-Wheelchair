/*
 * File: wheelchair_arduino.ino
 *
 * Project: TCNJ Autonomous Wheelchair
 * Component: Stage 1 - Communication Protocol
 *
 * Purpose:
 *   Receive newline-terminated text commands over the Arduino serial
 *   interface, validate them, and return a response.
 *
 * Supported commands:
 *   PING   -> OK,PONG
 *   STATUS -> OK,STATUS,PROTOCOL_READY
 *
 * Error responses:
 *   ERR,BAD_FORMAT
 *   ERR,UNKNOWN_COMMAND
 *   ERR,LINE_TOO_LONG
 *
 * IMPORTANT:
 *   This is communication-only firmware. It does not control motors,
 *   read sensors, or implement wheelchair motion.
 */

// ---------------------------------------------------------------------
// 1. CONFIGURATION
// ---------------------------------------------------------------------

// Communication speed, measured in bits per second.
//
// The Raspberry Pi software must eventually use the same baud rate.
// 115200 is our initial development choice, not a confirmed hardware
// requirement. We can change it if our final setup requires something
// different.
const unsigned long SERIAL_BAUD_RATE = 115200;

// Maximum number of command characters, excluding the newline.
//
// For example, "STATUS" is 6 characters.
// The buffer also needs one extra character for the terminating '\0'
// used by C-style strings.
const size_t MAX_COMMAND_LENGTH = 63;

// Buffer for accumulating one incoming command.
//
// A fixed-size buffer gives us a predictable memory requirement and
// prevents arbitrarily long incoming messages from growing in memory.
char commandBuffer[MAX_COMMAND_LENGTH + 1];

// Number of characters currently stored in commandBuffer.
size_t commandLength = 0;

// Set to true if an incoming line exceeds MAX_COMMAND_LENGTH.
//
// When this happens, the firmware discards the remainder of that line
// and reports an error when it reaches the newline.
bool lineTooLong = false;


// ---------------------------------------------------------------------
// 2. RESPONSE HELPERS
// ---------------------------------------------------------------------

/*
 * Send a successful response.
 *
 * Serial.println() appends a line ending, so the receiver can identify
 * where the response ends.
 */
void sendSuccess(const char* message)
{
    Serial.print("OK,");
    Serial.println(message);
}


/*
 * Send an error response.
 *
 * Error responses use a consistent format:
 *
 *   ERR,error_code
 *
 * This lets the future Raspberry Pi software distinguish protocol
 * errors from successful responses.
 */
void sendError(const char* errorCode)
{
    Serial.print("ERR,");
    Serial.println(errorCode);
}


// ---------------------------------------------------------------------
// 3. COMMAND PROCESSING
// ---------------------------------------------------------------------

/*
 * Process one complete command.
 *
 * The command is expected to be a null-terminated C-style string.
 * The newline has already been removed by the input-handling code.
 */
void processCommand(const char* command)
{
    // Ignore empty commands.
    //
    // For example, an empty line in the Serial Monitor should not
    // generate an error or cause any action.
    if (command[0] == '\0')
    {
        return;
    }

    // PING is a basic communication check.
    //
    // It confirms that a complete command reached the Arduino and that
    // the Arduino was able to process and respond to it.
    if (strcmp(command, "PING") == 0)
    {
        sendSuccess("PONG");
        return;
    }

    // STATUS reports the state of this communication firmware only.
    //
    // It does not confirm that the motors, sensors, battery, or other
    // wheelchair subsystems are operational.
    if (strcmp(command, "STATUS") == 0)
    {
        sendSuccess("STATUS,PROTOCOL_READY");
        return;
    }

    // Commands with commas are not supported in Stage 1.
    //
    // For example, "PING,123" includes an unsupported argument.
    // We reject it instead of silently accepting extra information.
    if (strchr(command, ',') != nullptr)
    {
        sendError("BAD_FORMAT");
        return;
    }

    // If execution reaches this point, the command is not recognized.
    //
    // Examples:
    //   START
    //   STOP
    //   ping
    //
    // These are not supported commands in this initial protocol.
    sendError("UNKNOWN_COMMAND");
}


// ---------------------------------------------------------------------
// 4. INPUT LINE HANDLING
// ---------------------------------------------------------------------

/*
 * Handle a single incoming character.
 *
 * Characters are collected until '\n' arrives. This approach allows
 * loop() to continue checking for input without waiting for an entire
 * command to arrive in one blocking read.
 */
void receiveCharacter(char incomingCharacter)
{
    // A newline marks the end of a command.
    if (incomingCharacter == '\n')
    {
        // If the command exceeded the buffer limit, report one error
        // and discard the entire oversized line.
        if (lineTooLong)
        {
            sendError("LINE_TOO_LONG");
        }
        else
        {
            // Add the null terminator so standard C string functions
            // such as strcmp() can safely examine the command.
            commandBuffer[commandLength] = '\0';

            // Some serial monitors send CRLF ("\r\n") instead of
            // just LF ("\n"). Remove a trailing carriage return so
            // that commands like "PING\r\n" are accepted.
            if (commandLength > 0 &&
                commandBuffer[commandLength - 1] == '\r')
            {
                commandBuffer[commandLength - 1] = '\0';
            }

            // Process the complete command.
            processCommand(commandBuffer);
        }

        // Reset the input state for the next command.
        commandLength = 0;
        lineTooLong = false;

        // The newline has been handled; no further processing needed.
        return;
    }

    // Once a line is oversized, ignore all additional characters until
    // its newline arrives. This prevents the remainder of that line
    // from being interpreted as a separate command.
    if (lineTooLong)
    {
        return;
    }

    // Store the character if space remains in the buffer.
    if (commandLength < MAX_COMMAND_LENGTH)
    {
        commandBuffer[commandLength] = incomingCharacter;
        commandLength++;
    }
    else
    {
        // The buffer is full. Mark this entire line as invalid.
        //
        // We do not write beyond the end of commandBuffer.
        lineTooLong = true;
    }
}


// ---------------------------------------------------------------------
// 5. ARDUINO INITIALIZATION
// ---------------------------------------------------------------------

void setup()
{
    // Start serial communication.
    //
    // Open the Serial Monitor at the same baud rate when testing.
    Serial.begin(SERIAL_BAUD_RATE);

    // Initialize the command parser's state.
    commandLength = 0;
    lineTooLong = false;

    // No motor pins or motor drivers are initialized in Stage 1.
}


// ---------------------------------------------------------------------
// 6. MAIN LOOP
// ---------------------------------------------------------------------

void loop()
{
    // Process every character currently waiting in the serial buffer.
    //
    // Checking Serial.available() before Serial.read() prevents the
    // code from attempting to read when no character is available.
    //
    // We intentionally do not add a delay here. The loop can continue
    // checking for incoming data as it becomes available.
    while (Serial.available() > 0)
    {
        // Read one character from the serial input buffer.
        char incomingCharacter = (char)Serial.read();

        // Add the character to the current line or process the line
        // if this character marks its end.
        receiveCharacter(incomingCharacter);
    }
}