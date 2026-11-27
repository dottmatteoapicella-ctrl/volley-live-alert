from volley_strategy import set_winner

def decode(row,best_of=None):
    """Do not infer match format or completed sets from an ambiguous feed."""
    if row.get("stale") is not False or row.get("awarded") is not False:
        return None
    status=row.get("status") or {}
    kind=status.get("type")
    if kind not in ("inprogress","finished"):
        return None
    if best_of not in (3,5):
        return None
    scores=[row.get(k) or {} for k in ("homeScore","awayScore")]
    totals=[s.get("current") for s in scores]
    if any(type(n) is not int or n<0 for n in totals):
        return None
    needed=best_of//2+1
    count=sum(totals)
    if count>best_of or max(totals)>needed:
        return None
    periods=[s.get("periods") or {} for s in scores]
    completed=[]
    for i in range(1,count+1):
        a,b=[p.get("period"+str(i)) for p in periods]
        w=set_winner(a,b,15 if i==best_of else 25)
        if w is None or max(completed.count(0),completed.count(1))>=needed:
            return None
        completed.append(w)
    if [completed.count(0),completed.count(1)]!=totals:
        return None
    if kind=="finished":
        if max(totals)!=needed or totals[0]==totals[1]:
            return None
        return completed,None,int(totals[1]>totals[0])
    if max(totals)>=needed or count>=best_of:
        return None
    if status.get("period")!="period"+str(count+1):
        return None
    current=tuple(p.get("period"+str(count+1)) for p in periods)
    if any(type(n) is not int or n<0 for n in current):
        current=None
    elif set_winner(*current,15 if count+1==best_of else 25) is not None:
        current=None
    return completed,current,None
