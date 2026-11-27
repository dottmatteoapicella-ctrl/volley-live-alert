"""Offline strategy engine. Scores must be verified by the provider adapter."""
def set_winner(a,b,target=25):
    if type(a) is not int or type(b) is not int or min(a,b)<0:
        return None
    if max(a,b)>=target and abs(a-b)>=2 and (max(a,b)==target or abs(a-b)==2):
        return int(b>a)
    return None

def signals(favorite, completed, current=None, best_of=5):
    """Completed contains verified set winners (0 home, 1 away).
    Current is the verified in-progress set score, not a completed set."""
    if favorite not in (0,1) or best_of not in (3,5) or any(x not in (0,1) for x in completed):
        return []
    needed=best_of//2+1
    if len(completed)>=best_of or max(completed.count(0),completed.count(1))>=needed:
        return []
    other=1-favorite
    out=[]
    if completed==[other]:
        out.append(("volley1",0))
    if completed==[other,other]:
        out.append(("volley2",0))
    if completed==[other,favorite]:
        out.append(("volley4",0))
    if current is not None and len(current)==2 and all(type(x) is int and x>=0 for x in current):
        target=15 if len(completed)==best_of-1 else 25
        if set_winner(*current,target) is None and current[other]-current[favorite]>=5:
            out.append(("volley3",len(completed)+1))
    return out

def outcome(strategy,favorite,set_number,completed,final_winner=None):
    if favorite not in (0,1):
        return None
    if strategy=="volley3":
        if not 1<=set_number<=len(completed):
            return None
        winner=completed[set_number-1]
    elif strategy in ("volley1","volley2","volley4"):
        winner=final_winner
    else:
        return None
    return winner==favorite if winner in (0,1) else None

def reserve(state,day,kind):
    if kind not in ("live","results"):
        return False
    if state.get("day")!=day:
        state.update(day=day,live=0,results=0,blocked=False)
    if state.get("blocked") or state["live"]+state["results"]>=90:
        return False
    if state[kind]>=(60 if kind=="live" else 30):
        return False
    state[kind]+=1
    return True
