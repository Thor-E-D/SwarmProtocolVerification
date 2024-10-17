def generate_function_is_int_in_list():
    return """
bool isIntInList(int tmpList[log_size], int possibleEntry) {
    int i = 0;
    for (i = 0; i &lt log_size; i++) {
        if (tmpList[i] == possibleEntry) {
            return true;
        } else if (tmpList[i] == 0) {
            return false;
        }
    }
    return false;
}
"""

def generate_function_add_int_to_list():
    return """
void addIntToList(int &amp;tmpList[logSize], int newEntry) {
    int i = 0;
    for (i = 0; i &lt; logSize; i++) {
        if (tmpList[i] == 0) {
            tmpList[i] = newEntry;
            return;
        }
    }
}
"""

def generate_function_set_next_log_to_propagate():
    return """
void setNextLogToPropagate() {
    if (amountOfPropagation &lt; amountOfLogs-2) {
        currentLogToPropagate = (currentLogToPropagate+1) % amountOfLogs;
        amountOfPropagation++;
    } else {
        // reset
        amountOfPropagation = -1;
    }
}
"""


def generate_function_get_order_count():
    return """
int getOrderCount() {
    int temp = eventOrderCounter;
    eventOrderCounter = eventOrderCounter + 1;
    return temp;
}
"""

def generate_function_set_log_entry_for_update():
    return """
void setLogEntryForUpdate(int eventID, int emitterID, int basedOnOrderCount, bool ignored) {
    tempLogEntry.eventID = eventID;
    tempLogEntry.emitterID = emitterID;
    tempLogEntry.orderCount = getOrderCount();
    tempLogEntry.basedOnOrderCount = basedOnOrderCount;
    tempLogEntry.tiedTo = -1;
    tempLogEntry.ignored = ignored;
}
"""

def generate_function_set_propagation_log():
    return """
void setPropagationLog(logEntryType tempLog[logSize]) {
    propagationLog = tempLog;
}
"""

def generate_function_find_and_set_tied_to():
    return """
void findAndSetTiedTo(logEntryType &amp;tempLog[logSize]) {
    int i;
    for(i = 0; i &lt; logSize; i++) {
        if (tempLog[i].orderCount != 0) {
            if (tempLog[i].emitterID == tempLogEntry.emitterID &amp;&amp; eventsTiedTo[tempLogEntry.eventID] == eventsTiedTo[tempLog[i].eventID]) {
                tempLogEntry.tiedTo = tempLog[i].tiedTo;
                return;
            }
        }
    }
    for(i = 0; i &lt; logSize; i++) {
        if (tempLog[i].orderCount != 0) {
            if (tempLog[i].eventID == eventsTiedTo[tempLogEntry.eventID]) {
                tempLogEntry.tiedTo = tempLog[i].orderCount;
                return;
            }
        }
    }  
}
"""