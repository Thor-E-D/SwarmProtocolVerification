"""\
String representation of all UPPAAL functions.
Most are static but some change depending on the given Swarm protocol (json files).

Note: length of arrays in UPPAAL most be hardcoded so some functions have the same 
functionality, but with different length of arrays.

"""

from typing import Dict

def generate_function_calculate_any_forced_to_propagte() -> str:
    return """
void calculateAnyForcedToPropagate() {
    int i = 0;
    bool tempAnyForcedToPropagate = false;
    for (i = 0; i &lt; amountOfLogs; i++) {
        tempAnyForcedToPropagate = tempAnyForcedToPropagate || forcedToPropagate[i];
    }
    anyForcedToPropagate = tempAnyForcedToPropagate;
}"""


def generate_function_is_in_subsciption() -> str:
    return """
bool isInSubsciptions(int tmpList[amountOfUniqueEvents], int possibleEntry) {
    int i = 0;
    for (i = 0; i &lt; amountOfUniqueEvents; i++) {
        if (tmpList[i] == possibleEntry) {
            return true;
        } else if (tmpList[i] == -1) {
            return false;
        }
    }
    return false;
}"""



def generate_function_is_int_in_list() -> str:
    return """
bool isIntInList(int tmpList[logSize], int possibleEntry) {
    int i = 0;
    for (i = 0; i &lt; logSize; i++) {
        if (tmpList[i] == possibleEntry) {
            return true;
        } else if (tmpList[i] == 0) {
            return false;
        }
    }
    return false;
}
"""

def generate_function_is_order_count_in_log() -> str:
    return """
bool isOrderCountInLog(logEntryType &amp;tempLog[logSize], int possibleEntry) {
    int i = 0;
    for (i = 0; i &lt; logSize; i++) {
        if (tempLog[i].orderCount == possibleEntry) {
            return true;
        } else if (tempLog[i].orderCount == 0) {
            return false;
        }
    }
    return false;
}"""

def generate_function_get_entry_from_order_count() -> str:
    return """
logEntryType getEntryFromOrderCount(int orderCount) {
    int i = 0;
    for (i = 0; i &lt; logSize; i++) {
        if (globalLog[i].orderCount == orderCount) {
            return globalLog[i];
        }
    }
    return globalLog[logSize-1];
}"""


def generate_function_add_int_to_list() -> str:
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

def generate_function_get_event_id_from_order_count() -> str:
    return """
int getEventIDfromOrderCount(int orderCount) {
    int i = 0;
    for (i = 0; i &lt; logSize; i++) {
        if (globalLog[i].orderCount == orderCount) {
            return globalLog[i].eventID;
        }
    }
    return -1;
}"""

def generate_function_set_next_log_to_propagate() -> str:
    return """
void setNextLogToPropagate() {
    if (amountOfPropagation &lt; amountOfLogs-2) {
        currentLogToPropagate = (currentLogToPropagate+1) % amountOfLogs;
        amountOfPropagation++;
    } else {
        // reset
        amountOfPropagation = 0;
    }
}
"""


def generate_function_get_order_count() -> str:
    return """
int getOrderCount() {
    int temp = eventOrderCounter;
    eventOrderCounter = eventOrderCounter + 1;
    return temp;
}
"""

def generate_function_set_log_entry_for_update() -> str:
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

def generate_function_find_difference_in_logs() -> str:
    return """
void findDifferenceInLogs(logEntryType &amp;oldLog[logSize], logEntryType &amp;newLog[logSize], bool &amp;didLogChange) {
    int i;
    for (i = 0; i &lt; logSize; i++) {
        if (oldLog[i].orderCount != newLog[i].orderCount) {
            didLogChange = true;
            return;
        } else if (oldLog[i].orderCount == 0) {
            return;
        }
    }
}"""

def generate_function_find_and_set_difference_in_logs() -> str:
    return """
void findAndSetDifferenceInLogs(logEntryType &amp;oldLog[logSize], logEntryType &amp;newLog[logSize], int &amp;logDifferenceEventIDs[logSize], int &amp;resetCount, int &amp;eventsToRead) {
    int i;
    int resetList[logSize] = logDifferenceEventIDs; // To reset logDifferenceEventIDs
    bool foundDifference = false;

    for (i = 0; i &lt; logSize; i++) {
        if (oldLog[i].orderCount != newLog[i].orderCount) {
            if (oldLog[i].orderCount == 0) {
                eventsToRead++;
                foundDifference = true;
            } else if (newLog[i].orderCount == 0) {
                logDifferenceEventIDs[resetCount] = oldLog[i].eventID;
                resetCount++;
                foundDifference = true;
            } else if (oldLog[i].eventID != newLog[i].eventID) {
                logDifferenceEventIDs[resetCount] = oldLog[i].eventID;
                eventsToRead++;
                resetCount++;
                foundDifference = true;
            } else if (foundDifference) {
                foundDifference = false;
                logDifferenceEventIDs = resetList;
                eventsToRead = 0;
                resetCount = 0;
            }
        } else if (oldLog[i].orderCount == 0 &amp;&amp; newLog[i].orderCount == 0) {
            return;
        } else if (foundDifference) { //We found a difference previously but have now found the same event in both logs again so we do not need to backtrack
            foundDifference = false;
            logDifferenceEventIDs = resetList;
            eventsToRead = 0;
            resetCount = 0;
        }
    }
}"""

def generate_function_find_tiedto() -> str:
    return """
int findTiedTo(logEntryType currentLogEntry, logEntryType &amp;tempLog[logSize]) {
    int j;
    int i;
    for(i = logSize-1; i &gt;= 0; i--) {
        if (tempLog[i].orderCount != 0) {
            for (j = 0; j&lt;maxAmountOfTied; j++) {
                if (tempLog[i].eventID == eventsTiedTo[currentLogEntry.eventID][j]  &amp;&amp; tempLog[i].orderCount != currentLogEntry.orderCount) {
                    return tempLog[i].orderCount;
                }
            }
        }
    }
    return -1;
}"""

def generate_function_set_propagation_log() -> str:
    return """
void setPropagationLog(logEntryType tempLog[logSize]) {
    propagationLog = tempLog;
}
"""

def generate_function_update_true_global_log() -> str:
    result = """
void updateTrueGlobalLog() {
    logEntryType tmpLogEntry = tempLogEntry;
    bool inCompetetion = false;
    inCompetetion = handleEvent(tmpLogEntry, trueGlobalLog, trueDiscardedEvents, trueDiscardedDueToCompetionEvents, trueCurrentIndex, globalCurrentLocation, globalEventLocationMap);
    if (tmpLogEntry.ignored == true) {
        if(inCompetetion) {
            addIntToList(trueDiscardedDueToCompetionEvents, tmpLogEntry.orderCount);
        } else if (isIntInList(trueDiscardedEvents, tmpLogEntry.basedOnOrderCount)) {
            addIntToList(trueDiscardedEvents, tmpLogEntry.orderCount);
        } else if (isIntInList(trueDiscardedDueToCompetionEvents, tmpLogEntry.basedOnOrderCount)) {
            addIntToList(trueDiscardedDueToCompetionEvents, tmpLogEntry.orderCount);
        } else {
            addIntToList(trueDiscardedEvents, tmpLogEntry.orderCount);
        }
        trueCurrentIndex--;
    } else {"""

    result += """
        trueGlobalLog[trueCurrentIndex] = tmpLogEntry;
    }
}"""

    return result


def generate_function_update_global_log() -> str:
    return """
void updateGlobalLog() {
    globalLog[globalLogIndex] = tempLogEntry;
    globalLogIndex++;
    trueCurrentIndex++;
    updateTrueGlobalLog();
}"""

def generate_function_update_log() -> str:
    return """
void updateLog(logEntryType &amp;tempLog[logSize]) {
    int i = 0;
    tempLogEntry.tiedTo = findTiedTo(tempLogEntry, tempLog);
    updateGlobalLog();
    for (i = 0; i &lt; logSize; i++) {
        if (tempLog[i].orderCount == 0) { // Log entry is unused since orderCount can never be 0
            tempLog[i] = tempLogEntry; // Update log
            return;
        }
    }
    return;
    // If we reach here log is full and we are in trouble
}
"""
def generate_function_is_In_branching_conflict() -> str:
    return """
bool isInBranchingConflict(int partition, int eventID) {
    int i = 0;
    for (i = 0; i &lt; innerSizeBranchingList; i++) {
        if (branchingList[partition][i] == eventID) {
            return true;
        }
    }
    return false;
}"""

def generate_function_consolidate_logs() -> str:
    return """
void consolidateLogs(logEntryType &amp;tmpLogEntry,logEntryType &amp;resLog[logSize], int &amp;discardedEvents[logSize], int &amp;discardedDueToCompetionEvents[logSize], logEntryType correctBranchEvent, int &amp;currentIndex, int &amp;currentLocation, int eventLocationMap[amountOfUniqueEvents][2]) {
    // move from discardedDueToCompetionEvents to discardedEvents and all basedOnEvents must be added to resLog.
    int i;
    int basedOnList[logSize];
    // First we find the other competing events and sort them correctly
    for (i = 0; i &lt; logSize; i++) {
        if (discardedDueToCompetionEvents[i] != 0) {
            // get the actual event
            logEntryType currentEvent = getEntryFromOrderCount(discardedDueToCompetionEvents[i]);
            if (isIntInList(basedOnList, currentEvent.basedOnOrderCount)) {
                resLog[currentIndex] = currentEvent;
                addIntToList(basedOnList, currentEvent.orderCount);
                discardedDueToCompetionEvents[i] = 0;
                currentIndex++;
                if (eventLocationMap[currentEvent.eventID][0] == currentLocation) {
                    currentLocation = eventLocationMap[currentEvent.eventID][1];
                }
            } else if (isBranchingList[currentEvent.eventID]) {
                if (isInBranchingConflict(isInBranchingPartion[currentEvent.eventID], correctBranchEvent.eventID) &amp;&amp; correctBranchEvent.basedOnOrderCount == currentEvent.basedOnOrderCount &amp;&amp; correctBranchEvent.tiedTo == currentEvent.tiedTo) {
                    if (isIntInList(trueDiscardedEvents, currentEvent.orderCount)) {
                        addIntToList(discardedEvents, currentEvent.orderCount);
                        addIntToList(basedOnList, currentEvent.orderCount);
                        discardedDueToCompetionEvents[i] = 0;
                    }
                }
            }
        } 
        if (discardedEvents[i] != 0) {
            logEntryType currentEvent = getEntryFromOrderCount(discardedEvents[i]);
            if (isBranchingList[currentEvent.eventID]) {
                if (isInBranchingConflict(isInBranchingPartion[currentEvent.eventID], correctBranchEvent.eventID) &amp;&amp; correctBranchEvent.basedOnOrderCount == currentEvent.basedOnOrderCount &amp;&amp; correctBranchEvent.tiedTo == currentEvent.tiedTo) {
                    if (isIntInList(trueDiscardedDueToCompetionEvents, currentEvent.orderCount)) {
                        addIntToList(discardedDueToCompetionEvents, currentEvent.orderCount);
                        discardedEvents[i] = 0;
                    }
                }
            }
        } 
        if (discardedDueToCompetionEvents[i] != 0 &amp;&amp; discardedDueToCompetionEvents[i] != 0) {
            i = logSize;
        }
    }
}"""

def generate_function_check_and_fix_branch_competetion() -> str:
    return """
void checkAndFixBranchCompetetion(logEntryType &amp;tmpLogEntry,logEntryType &amp;resLog[logSize], int &amp;discardedEvents[logSize], int &amp;discardedDueToCompetionEvents[logSize], int &amp;currentIndex, int &amp;currentLocation, int eventLocationMap[amountOfUniqueEvents][2]) {
    int i;
    // we know we are going to return true to in competetion
    // Check if we have witnessed the correct event
    for (i = 0; i &lt; logSize; i++) {
        if (trueGlobalLog[i].orderCount != 0) {
            if (isInBranchingConflict(isInBranchingPartion[tmpLogEntry.eventID], trueGlobalLog[i].eventID) &amp;&amp; trueGlobalLog[i].basedOnOrderCount == tmpLogEntry.basedOnOrderCount &amp;&amp; trueGlobalLog[i].tiedTo == tmpLogEntry.tiedTo) {
                if (isOrderCountInLog(resLog, trueGlobalLog[i].eventID)) {
                    // Consolidate
                    consolidateLogs(tmpLogEntry, resLog, discardedEvents, discardedDueToCompetionEvents, trueGlobalLog[i], currentIndex, currentLocation, eventLocationMap);
                }
            }
        }
    }
}"""



def generate_function_handle_branching_event() -> str:
    return"""
bool handleBranchingEvent(logEntryType &amp;tmpLogEntry,logEntryType &amp;resLog[logSize], int &amp;discardedEvents[logSize], int &amp;discardedDueToCompetionEvents[logSize], int &amp;currentIndex, int &amp;currentLocation, int eventLocationMap[amountOfUniqueEvents][2]) {
    int j;
    if (isIntInList(discardedDueToCompetionEvents, tmpLogEntry.basedOnOrderCount)) {
        tmpLogEntry.ignored = true;
    }
    //Need to check if looping cause then we would accept it if is basedOn is in discardedEvents
    if (isIntInList(discardedEvents, tmpLogEntry.tiedTo)) {
        int tiedToEventID = getEventIDfromOrderCount(tmpLogEntry.tiedTo);
        if (isInBranchingPartion[tmpLogEntry.eventID] != isInBranchingPartion[tiedToEventID]) {
            tmpLogEntry.ignored = true;
        }
    }
    
    for (j = currentIndex - 1; j &gt;= 0; j--) {
        // Occours when we are merging two logs and a new event is in the same branchpartition as one already accepted in the result of the merged log.
        // If this happens we have to check if we need to move some discarded events around
        if(isInBranchingConflict(isInBranchingPartion[tmpLogEntry.eventID], resLog[j].eventID)) {
            if (!isIntInList(discardedEvents, resLog[j].orderCount)) {
                if (tmpLogEntry.eventID == resLog[j].eventID) { //Same one so does not need to ignore branch
                    tmpLogEntry.ignored = true;
                    return false;
                }
                // if in competetion we have to check if correct
                checkAndFixBranchCompetetion(tmpLogEntry, resLog, discardedEvents, discardedDueToCompetionEvents, currentIndex, currentLocation, eventLocationMap);
                tmpLogEntry.ignored = true;
                return true;
            }
        }
    }
    return false;
}"""

def generate_function_handle_event() -> str:
    return """
bool handleEvent(logEntryType &amp;currentLogEntry,logEntryType &amp;resLog[logSize], int &amp;discardedEvents[logSize], int &amp;discardedDueToCompetionEvents[logSize], int &amp;currentIndex, int &amp;currentLocation, int eventLocationMap[amountOfUniqueEvents][2]) {
    int i;

    // Branch tracking
    if (branchTrackingEnabled) {
        int shouldTieTo;
        shouldTieTo = findTiedTo(currentLogEntry, resLog);
        if (shouldTieTo != currentLogEntry.tiedTo) {
            currentLogEntry.ignored = true;
            return true;
        }
    }

    if (eventLocationMap[currentLogEntry.eventID][0] != currentLocation) {
        if (eventLocationMap[currentLogEntry.eventID][0] != -1) { //In subsciptions
            currentLogEntry.ignored = true;
        }

        if (isBranchingList[currentLogEntry.eventID]) {
            return handleBranchingEvent(currentLogEntry, resLog, discardedEvents, discardedDueToCompetionEvents, currentIndex, currentLocation, eventLocationMap);
        }
        if (isIntInList(discardedDueToCompetionEvents, currentLogEntry.basedOnOrderCount)) {
            currentLogEntry.ignored = true;
            return false;
        }

        return false;
    } else {
        if (isIntInList(discardedDueToCompetionEvents, currentLogEntry.basedOnOrderCount)) {
            currentLogEntry.ignored = true;
            return false;
        }
        // Even if correct it might still be in competetion
        // Have to check for single loop edge case.
        if (!isBranchingList[currentLogEntry.eventID] &amp;&amp; eventLocationMap[currentLogEntry.eventID][0] != eventLocationMap[currentLogEntry.eventID][1]) {
            for (i = currentIndex - 1; i &gt;= 0; i--) {
                if (resLog[i].eventID == currentLogEntry.eventID &amp;&amp; (resLog[i].tiedTo == currentLogEntry.tiedTo || resLog[i].basedOnOrderCount == currentLogEntry.basedOnOrderCount)) {
                    currentLogEntry.ignored = true;
                    return false;
                }
            }
        }
        currentLocation = eventLocationMap[currentLogEntry.eventID][1];
    }
    return false;
}"""


# This function expects the name of the function and a map of what other event each event is based on
def generate_function_update_log_entry() -> str:
    function_str = f"""
void updateLogEntry(logEntryType &amp;tempLog[logSize], int &amp;emittedOrderCounts[logSize], int log_id_start) {{    
    addIntToList(emittedOrderCounts, tempLogEntry.orderCount);
    // We check if basedemitterID set to -2 as this is a flag for unknown
    currentLogEntryEmitterID = tempLogEntry.emitterID;
    tempLogEntry.emitterID = tempLogEntry.emitterID + log_id_start;
    if (tempLogEntry.basedOnOrderCount == -2) {{
        int i = 0;
        for (i = logSize-1; i &gt;= 0; i--) {{
            if (tempLog[i].orderCount != 0) {{ 
                tempLogEntry.basedOnOrderCount = tempLog[i].orderCount;
                updateLog(tempLog);
                return;
            }}
        }}
    }}
    tempLogEntry.basedOnOrderCount = -1;
    updateLog(tempLog);
    return;
}}"""
    return function_str

def generate_function_handle_log_entry(own_events: list[str], other_events: list[str]) -> str:
    function_str = """
logEntryType handleLogEntry(logEntryType tmpLogEntry,logEntryType &amp;resLog[logSize], int &amp;currentIndex) {
    // We first find the event Type
    int currentEventType = tmpLogEntry.eventID;\n"""
    
    first = True
    for event in other_events:
        if first:
            function_str += f"    if (currentEventType == {event}) {{\n"
            first = False
        else:
            function_str += f" else if (currentEventType == {event}) {{\n"
        function_str += "        inCompetetion = handleEvent(tmpLogEntry, resLog, discardedEvents, discardedDueToCompetionEvents, currentIndex, currentLocation, eventLocationMap);\n"
        function_str += "    }"
    
    for event in own_events:
        if first:
            function_str += f"    if (currentEventType == {event}) {{\n"
            first = False
        else:
            function_str += f" else if (currentEventType == {event}) {{\n"
        function_str += "        inCompetetion = handleEvent(tmpLogEntry, resLog, discardedEvents, discardedDueToCompetionEvents, currentIndex, currentLocation, eventLocationMap);\n"
        function_str += "    }"
    
    function_str += f" else {{\n"
    function_str += "        tmpLogEntry.ignored = true;\n"
    function_str += "    }"


    function_str += "\n    return tmpLogEntry;\n"
    function_str += "}\n"
    
    return function_str

def generate_function_merge_propagation_log() -> str:
    function_str = """
void mergePropagationLog() {
    int currentLogCounter = 0;
    int propagatedLogCounter = 0;

    logEntryType resLog[logSize];

    logEntryType currentLogEntry;
    logEntryType propagatedLogEntry;
    logEntryType tmpLogEntry;

    bool currentLogDone = false;
    bool propagatedLogDone = false;
    bool newEventConsidered = false;

    int i;
    currentLocation = initialLocation;
    for (i = 0; i &lt; (logSize * 2); i++) {
        currentLogEntry = currentLog[currentLogCounter];
        propagatedLogEntry = propagationLog[propagatedLogCounter];
        
        // TODO if one is done then we can simply append the rest
        if (currentLogEntry.orderCount == 0) {
            currentLogDone = true;
        }
        if (propagatedLogEntry.orderCount == 0) {
            propagatedLogDone = true;
        }

        // If both are done we are done.
        if (currentLogDone &amp;&amp; propagatedLogDone) {
            if (currentSizeOfLog != i) {
                currentSizeOfLog = i;
                didLogChange = true;
            } else {
                findDifferenceInLogs(currentLog, resLog, didLogChange);
            }

            if (didLogChange) {
                findAndSetDifferenceInLogs(currentLog, resLog, discardedEventIDs, resetCount, eventsToRead);
            }

            currentLog = resLog;
            return;
        }
        
        // If one entry is invalid then we have to choose the other one
        if (currentLogDone) {
            propagatedLogCounter++;
            tmpLogEntry = propagatedLogEntry;
            newEventConsidered = true;
        } else if (propagatedLogDone) {
            currentLogCounter++;
            tmpLogEntry = currentLogEntry;
        } else if (propagatedLogEntry.orderCount == currentLogEntry.orderCount) { //They are the same event we use one but skip both
            propagatedLogCounter++;
            currentLogCounter++;
            tmpLogEntry = currentLogEntry;
        } else if (currentLogEntry.orderCount &gt; propagatedLogEntry.orderCount) { // Both entries are valid we can now figure out which one is first
            propagatedLogCounter++;
            tmpLogEntry = propagatedLogEntry;
            newEventConsidered = true;
        } else {
            currentLogCounter++;
            tmpLogEntry = currentLogEntry;
        }
        
        // If it was already ignored we don't have to add it else we have to handle it
        if (isIntInList(discardedEvents, tmpLogEntry.orderCount) || isIntInList(discardedDueToCompetionEvents, tmpLogEntry.orderCount) || isOrderCountInLog(resLog,tmpLogEntry.orderCount)) {
            i--;
        } else if (!newEventConsidered) {
            currentLocation = eventLocationMap[tmpLogEntry.eventID][1];
            resLog[i] = tmpLogEntry;
        } else {
            int priorIndex = i;
            tmpLogEntry = handleLogEntry(tmpLogEntry,resLog,i);
            if (i != priorIndex) {
                newUpdates = true;
            }"""

    function_str += """
            if (olderEntryIgnored) {
                int j;
                int h = 0;
                logEntryType tmpLog[logSize];
                for(j = 0; j &lt; logSize; j++) {
                    if (resLog[j].orderCount == 0) {
                        j = logSize;
                    } else if (!resLog[j].ignored) {
                        tmpLog[h] = resLog[j];
                        h++;
                    } else {
                        i--;
                        addIntToList(discardedEvents, resLog[j].orderCount);
                    }
                }
                resLog = tmpLog;
                olderEntryIgnored = false;
            }"""

    function_str += """
        if (tmpLogEntry.ignored) {
                // Value should be discarded
                i--;"""

    function_str += """
                if(inCompetetion) {
                    addIntToList(discardedDueToCompetionEvents, tmpLogEntry.orderCount);
                    inCompetetion = false;
                } else if (isIntInList(discardedEvents, tmpLogEntry.basedOnOrderCount)) {
                    addIntToList(discardedEvents, tmpLogEntry.orderCount);
                } else if (isIntInList(discardedDueToCompetionEvents, tmpLogEntry.basedOnOrderCount)) {
                    addIntToList(discardedDueToCompetionEvents, tmpLogEntry.orderCount);
                } else {
                    addIntToList(discardedEvents, tmpLogEntry.orderCount);
                }
            } else {
                resLog[i] = tmpLogEntry;
            }

        }
    }
}
"""
    return function_str