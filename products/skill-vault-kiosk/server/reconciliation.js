function csvCell(value){
  const s=String(value??'');
  return /[\",\n]/.test(s)?`\"${s.replace(/\"/g,'\"\"')}\"`:s;
}
function buildReconciliationCsv({state,config}){
  const rows=[['metric','value','classification']];
  rows.push(['payments_enabled',config.paymentsEnabled,'configuration']);
  rows.push(['demo_plays',state.counters.demoPlays||0,'non-revenue']);
  rows.push(['paid_plays',state.counters.paidPlays||0,'actual only after provider authorization']);
  rows.push(['actual_collected_cents',state.counters.collectedCents||0,'actual']);
  rows.push(['tickets_awarded',state.counters.awardedTickets||0,'liability']);
  rows.push(['tickets_redeemed',state.counters.redeemedTickets||0,'liability']);
  const modeled=(state.counters.demoPlays+state.counters.paidPlays)*config.playPriceCents;
  rows.push(['modeled_gross_cents',modeled,'planning only']);
  rows.push(['modeled_owner_share_cents',Math.round(modeled*config.ownerSharePct/100),'planning only']);
  rows.push(['modeled_venue_share_cents',Math.round(modeled*config.venueSharePct/100),'planning only']);
  return rows.map(r=>r.map(csvCell).join(',')).join('\n')+'\n';
}
module.exports={buildReconciliationCsv};
