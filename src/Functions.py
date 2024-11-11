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
        amountOfPropagation = -1;
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

def generate_function_find_and_set_tiedto() -> str:
    return """
void findAndSetTiedTo(logEntryType &amp;tempLog[logSize]) {
    int k;
    int j;
    int i;
    for(i = logSize-1; i &gt;= 0; i--) {
        if (tempLog[i].orderCount != 0) {
            for (j = 0; j&lt;maxAmountOfTied; j++) {
                if (tempLog[i].eventID == eventsTiedTo[tempLogEntry.eventID][j] &amp;&amp; tempLog[i].tiedTo != -1) {
                    tempLogEntry.tiedTo = tempLog[i].orderCount;
                    return;
                }
            }
        }
    }
    for(i = logSize-1; i &gt;= 0; i--) {
        if (tempLog[i].orderCount != 0) {
            if (tempLog[i].emitterID == tempLogEntry.emitterID) {
                for (j = 0; j&lt;maxAmountOfTied; j++) {
                    for (k = 0; k&lt;maxAmountOfTied; k++) {
                        if (eventsTiedTo[tempLogEntry.eventID][j] == eventsTiedTo[tempLog[i].eventID][k] &amp;&amp; tempLog[i].tiedTo != -1) {
                            tempLogEntry.tiedTo = tempLog[i].tiedTo;
                            return;
                        }
                    }
                }
            }
        }
    }
    for(i = logSize-1; i &gt;= 0; i--) {
        if (tempLog[i].orderCount != 0) {
            for (j = 0; j&lt;maxAmountOfTied; j++) {
                if (tempLog[i].eventID == eventsTiedTo[tempLogEntry.eventID][j]) {
                    tempLogEntry.tiedTo = tempLog[i].orderCount;
                    return;
                }
            }
        }
    }  
}"""

def generate_function_set_propagation_log() -> str:
    return """
void setPropagationLog(logEntryType tempLog[logSize]) {
    propagationLog = tempLog;
}
"""

def generate_function_update_global_log() -> str:
    return """
void updateGlobalLog() {
    int i;
    logEntryType resLog[logSize];
    int count = 0;
    bool addedEntry = false;

    for (i = 0; i &lt; (logSize); i++) {
        if (globalLog[count].orderCount == 0) {
            if (addedEntry) {
                resLog[i] = globalLog[count];
                globalLog = resLog;
                return;
            }
            resLog[i] = tempLogEntry;
            globalLog = resLog;
            return;
        }
        else if (globalLog[count].orderCount &gt; tempLogEntry.orderCount) {
            resLog[i] = tempLogEntry;
            count = count - 1;
            addedEntry = true;
        } else {
            resLog[i] = globalLog[count];
        }
        count = count + 1;
    }
    globalLog = resLog;
}"""

def generate_function_update_log() -> str:
    return """
void updateLog(logEntryType &amp;tempLog[logSize]) {
    int i = 0;
    findAndSetTiedTo(tempLog);
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

def generate_function_handle_branching_event() -> str:
    return """
void handleBranchingEvent(logEntryType &amp;tmpLogEntry,logEntryType &amp;resLog[logSize], int currentIndex) {
    int j;
    for (j = currentIndex; j &gt;= 0; j--) {
        if (resLog[j].tiedTo == tmpLogEntry.tiedTo &amp;&amp; tmpLogEntry.basedOnOrderCount == resLog[j].basedOnOrderCount) {
            if(isInBranchingConflict(isInBranchingPartion[tmpLogEntry.eventID], tmpLogEntry.eventID)) {
                tmpLogEntry.ignored = true;
            }
        }
    }
}"""


def generate_function_handle_own_event() -> str:
    return """
bool handleOwnEvent(logEntryType &amp;tmpLogEntry,logEntryType &amp;resLog[logSize], int &amp;discardedEvents[logSize], int currentIndex, int id) {
    if (isBranchingList[tmpLogEntry.eventID]) {
        handleBranchingEvent(tmpLogEntry, resLog, currentIndex);
    }
    if (isIntInList(discardedEvents, tmpLogEntry.basedOnOrderCount)) {
        tmpLogEntry.ignored = true;
    } else if (tmpLogEntry.emitterID != id) {
        int j;
        tmpLogEntry.ignored = true;
        // Check if we have already tied into this so an event we emitted that is tied to the same thing
        for (j = currentIndex; j &gt;= 0; j--) {
            if (resLog[j].emitterID == id &amp;&amp; resLog[j].eventID == tmpLogEntry.eventID &amp;&amp; resLog[j].tiedTo == tmpLogEntry.tiedTo) {
                return false;
                }
        }
        for (j = currentIndex; j &gt;= 0; j--) {
            if (resLog[j].tiedTo == tmpLogEntry.tiedTo || tmpLogEntry.tiedTo == resLog[j].orderCount) {
                resLog[j].ignored = true;
            }
        }
        return true; 
    }
    return false;
}
"""

def generate_function_handle_other_event() -> str:
    return """
void handleOtherEvent(logEntryType &amp;tmpLogEntry,logEntryType &amp;resLog[logSize], int &amp;discardedEvents[logSize], int &amp;subsciptions[amountOfUniqueEvents], int currentIndex) {
    int i;
    if (isBranchingList[tmpLogEntry.eventID]) {
        handleBranchingEvent(tmpLogEntry, resLog, currentIndex);
    }
    if ((isInSubsciptions(subsciptions, getEventIDfromOrderCount(tmpLogEntry.basedOnOrderCount)) &amp;&amp; isIntInList(discardedEvents, tmpLogEntry.basedOnOrderCount)) || isIntInList(discardedEvents, tmpLogEntry.tiedTo)) {
        tmpLogEntry.ignored = true;
    }
    
    for (i = currentIndex; i &gt;= 0; i--) {
        if (tmpLogEntry.tiedTo != -1 &amp;&amp; resLog[i].eventID == tmpLogEntry.eventID &amp;&amp; resLog[i].tiedTo == tmpLogEntry.tiedTo) {
            tmpLogEntry.ignored = true;
        }
    }
}
"""

# This function expects the name of the function and a map of what each event is based on
def generate_function_update_log_name(name: str, event_condition_map: dict[str, list[str]]) -> str:
    function_str = f"""
void updateLog{name}(logEntryType &amp;tempLog[logSize], int &amp;emittedOrderCounts[logSize], int log_id_start) {{    
    addIntToList(emittedOrderCounts, tempLogEntry.orderCount);
    // We check if basedemitterID set to -2 as this is a flag for unknown
    tempLogEntry.emitterID = tempLogEntry.emitterID + log_id_start;
    if (tempLogEntry.basedOnOrderCount == -2) {{
        int i = 0;
        for (i = logSize-1; i &gt;= 0; i--) {{
            if (tempLog[i].orderCount == 0) {{
            }} else {{ 
                """
    
    first = True
    for outer_event, inner_events in event_condition_map.items():
        if first:
            function_str += f"if (tempLogEntry.eventID == {outer_event}) {{\n"
            first = False
        else:
            function_str += f" else if (tempLogEntry.eventID == {outer_event}) {{\n"

        # For each outer_event, handle the list of inner_events
        if len(inner_events) == 1:
            function_str += f"                    if (tempLog[i].eventID == {inner_events[0]}) {{\n"
        else:
            conditions = " || ".join([f"tempLog[i].eventID == {event}" for event in inner_events])
            function_str += f"                    if ({conditions}) {{\n"

        function_str += """                        tempLogEntry.basedOnOrderCount = tempLog[i].orderCount;
                        updateLog(tempLog);
                        return;
                    }
                }"""

    function_str += """
            }
        }
    }
    tempLogEntry.basedOnOrderCount = -1;
    updateLog(tempLog);
    return;
}"""
    return function_str

def generate_function_handle_log_entry(own_events: list[str], other_events: list[str]) -> str:
    function_str = """
logEntryType handleLogEntry(logEntryType tmpLogEntry,logEntryType &amp;resLog[logSize], int currentIndex) {
    // We first find the event Type
    int currentEventType = tmpLogEntry.eventID;\n"""
    
    # Generate the "other" events handling with `handleOtherEvent`
    first = True
    for event in other_events:
        if first:
            function_str += f"    if (currentEventType == {event}) {{\n"
            first = False
        else:
            function_str += f" else if (currentEventType == {event}) {{\n"
        function_str += "        handleOtherEvent(tmpLogEntry, resLog, discardedEvents, subscriptions, currentIndex);\n"
        function_str += "    }"
    
    # Generate the "own" events handling with `handleOwnEvent`
    for event in own_events:
        function_str += f" else if (currentEventType == {event}) {{\n"
        function_str += "        olderEntryIgnored = handleOwnEvent(tmpLogEntry, resLog, discardedEvents, currentIndex, id + log_id_start);\n"
        function_str += "    }"
    
    function_str += f" else {{\n"
    function_str += "        tmpLogEntry.ignored = true;\n"
    function_str += "    }"


    # Finish the function
    function_str += "\n    return tmpLogEntry;\n"
    function_str += "}\n"
    
    return function_str

def generate_function_merge_propagation_log(evetname_loopcounter) -> str:
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

    int i;
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
            currentLog = resLog; 
            return;
        }
        
        // If one entry is invalid then we have to choose the other one
        if (currentLogDone) {
            propagatedLogCounter++;
            tmpLogEntry = propagatedLogEntry;
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
        } else {
            currentLogCounter++;
            tmpLogEntry = currentLogEntry;
        }
        
        // If it was already ignored we don't have to add it else we have to handle it
        if (isIntInList(discardedEvents, tmpLogEntry.orderCount)) {
            i--;
        } else {
            tmpLogEntry = handleLogEntry(tmpLogEntry,resLog,i-1);
            if (tmpLogEntry.ignored) {
                // Value should be discarded """

    for event_name in evetname_loopcounter:
        function_str += f"""                
                if (tmpLogEntry.eventID == {event_name} &amp;&amp; tmpLogEntry.emitterID == id + log_id_start) {{
                    {evetname_loopcounter[event_name]} = {evetname_loopcounter[event_name]} - 1;
                }}"""


    function_str += """
                i--;
                addIntToList(discardedEvents, tmpLogEntry.orderCount);
            } else {
                resLog[i] = tmpLogEntry;
            }
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
            }


        }
    }
}
"""
    return function_str