-- Tennis Booking Automation App
-- This application runs the tennis booking script and schedules itself for the next day

on run
    set logFile to "/Users/willwallwan/Documents/GitHub/Octogon/app_log.txt"
    
    -- Log start time
    my logMessage(logFile, "==================================")
    my logMessage(logFile, "Tennis Booker App started at " & (current date))
    
    -- Run the tennis booking script directly with shell command
    my logMessage(logFile, "Launching tennis booking script...")
    
    try
        -- Run the fixed shell script that uses the virtual environment
        do shell script "cd /Users/willwallwan/Documents/GitHub/Octogon && zsh run_tennis_booker_fixed.sh"
        my logMessage(logFile, "Tennis booking script completed successfully")
    on error errMsg
        my logMessage(logFile, "Error running tennis booking script: " & errMsg)
    end try
    
    -- Schedule the next day's run using shell commands
    my logMessage(logFile, "Scheduling tomorrow's booking...")
    
    try
        -- Clear any existing scheduled jobs
        do shell script "for job in $(atq | cut -f1); do atrm $job; done"
        
        -- Schedule the app to run tomorrow
        do shell script "echo 'open -a \"/Users/willwallwan/Documents/GitHub/Octogon/TennisBooker.app\"' | at 8:00AM tomorrow"
        
        -- Get the job number for logging
        set jobOutput to do shell script "atq"
        my logMessage(logFile, "Scheduled for tomorrow at 8:00AM")
        my logMessage(logFile, "Current jobs: " & jobOutput)
    on error errMsg
        my logMessage(logFile, "Error scheduling next run: " & errMsg)
    end try
    
    my logMessage(logFile, "Tennis Booker App completed at " & (current date))
    my logMessage(logFile, "==================================")
end run

-- Helper function to log messages
on logMessage(logFile, message)
    do shell script "echo \"" & message & "\" >> \"" & logFile & "\""
end logMessage 