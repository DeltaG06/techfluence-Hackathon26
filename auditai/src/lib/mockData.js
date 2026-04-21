export const anomalies = [
  {
    id: "TXN-8924",
    amount: "$24,500.00",
    vendor: "Acme Cloud Services",
    department: "Engineering",
    employee: "Sarah Chen",
    timestamp: "Today, 10:42 AM",
    riskLevel: "HIGH",
    explanation: "New vendor, no prior history. Amount is 7x dept average.",
    category: "Software Subscriptions",
    anomalyScore: 94,
    evidence: [
      "No prior vendor history",
      "7x department average",
      "Submitted Sunday 11:47 PM",
      "Policy FIN-12 violated — no procurement approval"
    ],
    narrative: "This transaction exhibits multiple high-risk indicators consistent with bypass of standard procurement controls. The vendor 'Acme Cloud Services' has no prior relationship with the organization, yet the initial billing amount of $24,500 significantly exceeds the Engineering department's average software subscription cost ($3,500). Furthermore, the transaction was submitted outside of normal business hours (Sunday at 11:47 PM) by Sarah Chen. There is no recorded pre-approval matching Policy FIN-12 requirements. It is highly recommended to pause payment and escalate to the Department Head for manual verification."
  },
  {
    id: "TXN-8910",
    amount: "$8,250.00",
    vendor: "Global Logistics Inc.",
    department: "Operations",
    employee: "Michael Ross",
    timestamp: "Today, 09:15 AM",
    riskLevel: "MEDIUM",
    explanation: "Duplicate invoice detected. Similar amount paid 3 days ago.",
    category: "Shipping & Freight",
    anomalyScore: 76,
    evidence: [
      "Exact amount match with TXN-8842",
      "Same vendor within 7-day window",
      "Invoice number is sequential (INV-4402 vs INV-4401)"
    ],
    narrative: "The system flagged this transaction as a potential duplicate payment. An identical amount ($8,250.00) was paid to 'Global Logistics Inc.' just 3 days prior under transaction TXN-8842. The invoice numbers are sequential, which often indicates a double-submission error rather than malicious intent. Reviewing the attached invoice documents is advised before proceeding with payment."
  },
  {
    id: "TXN-8899",
    amount: "$1,200.00",
    vendor: "WeWork Office Space",
    department: "Sales",
    employee: "Jessica Day",
    timestamp: "Yesterday, 04:30 PM",
    riskLevel: "LOW",
    explanation: "Slightly higher than normal monthly recurring charge.",
    category: "Real Estate",
    anomalyScore: 42,
    evidence: [
      "Amount is 15% higher than previous 6 months",
      "Vendor is known and trusted"
    ],
    narrative: "This transaction was flagged due to a minor deviation from the established baseline. The charge from 'WeWork Office Space' is $1,200, which is approximately 15% higher than the historical monthly average of $1,040 for this employee. This is a low-risk event and is likely due to an added service fee or minor rate increase. Minimal review is necessary."
  },
  {
    id: "TXN-8875",
    amount: "$54,000.00",
    vendor: "Offshore Consulting LLC",
    department: "Executive",
    employee: "David Wallace",
    timestamp: "Yesterday, 02:10 PM",
    riskLevel: "HIGH",
    explanation: "Large round-number transaction to flagged jurisdiction.",
    category: "Professional Services",
    anomalyScore: 98,
    evidence: [
      "Vendor registered in high-risk jurisdiction",
      "Exact round number amount ($54,000.00)",
      "First transaction with vendor",
      "No matching SOW found in contract database"
    ],
    narrative: "A critical anomaly has been detected involving a high-value transfer of $54,000 to 'Offshore Consulting LLC'. The vendor is newly registered in a jurisdiction previously flagged for compliance risks. The use of a large, exact round number is statistically rare for professional services invoices. Additionally, cross-referencing with the legal database yielded no active Statement of Work (SOW). Immediate escalation and freeze of funds are strongly advised."
  },
  {
    id: "TXN-8862",
    amount: "$450.00",
    vendor: "Uber Eats",
    department: "Marketing",
    employee: "Tom Haverford",
    timestamp: "Oct 24, 08:22 PM",
    riskLevel: "MEDIUM",
    explanation: "Unusually high meal expense for a single day.",
    category: "Meals & Entertainment",
    anomalyScore: 65,
    evidence: [
      "Exceeds daily meal allowance by 400%",
      "Late evening submission",
      "No client attendees listed"
    ],
    narrative: "This expense report for $450.00 on 'Uber Eats' significantly exceeds the company's daily meal allowance of $90. The expense was submitted without listing any client attendees, which is required for meals exceeding $100. While the vendor is common, the amount requires manager justification to ensure policy compliance."
  }
];

export const spendTrendData = [
  { date: 'Oct 01', spend: 12000, isAnomaly: false },
  { date: 'Oct 02', spend: 14500, isAnomaly: false },
  { date: 'Oct 03', spend: 11000, isAnomaly: false },
  { date: 'Oct 04', spend: 13200, isAnomaly: false },
  { date: 'Oct 05', spend: 9000, isAnomaly: false },
  { date: 'Oct 06', spend: 8500, isAnomaly: false },
  { date: 'Oct 07', spend: 15000, isAnomaly: false },
  { date: 'Oct 08', spend: 16200, isAnomaly: false },
  { date: 'Oct 09', spend: 14800, isAnomaly: false },
  { date: 'Oct 10', spend: 42000, isAnomaly: true },
  { date: 'Oct 11', spend: 13000, isAnomaly: false },
  { date: 'Oct 12', spend: 11500, isAnomaly: false },
  { date: 'Oct 13', spend: 10000, isAnomaly: false },
  { date: 'Oct 14', spend: 14000, isAnomaly: false },
  { date: 'Oct 15', spend: 15500, isAnomaly: false },
  { date: 'Oct 16', spend: 16000, isAnomaly: false },
  { date: 'Oct 17', spend: 38000, isAnomaly: true },
  { date: 'Oct 18', spend: 12500, isAnomaly: false },
  { date: 'Oct 19', spend: 9500, isAnomaly: false },
  { date: 'Oct 20', spend: 8800, isAnomaly: false },
  { date: 'Oct 21', spend: 13500, isAnomaly: false },
  { date: 'Oct 22', spend: 14200, isAnomaly: false },
  { date: 'Oct 23', spend: 15100, isAnomaly: false },
  { date: 'Oct 24', spend: 54000, isAnomaly: true },
  { date: 'Oct 25', spend: 16500, isAnomaly: false },
  { date: 'Oct 26', spend: 11200, isAnomaly: false },
  { date: 'Oct 27', spend: 10500, isAnomaly: false },
  { date: 'Oct 28', spend: 14800, isAnomaly: false },
  { date: 'Oct 29', spend: 15200, isAnomaly: false },
  { date: 'Oct 30', spend: 16800, isAnomaly: false }
];

export const topAnomalousDays = [
  { date: 'Oct 24, 2026', amount: '$54,000.00', riskLevel: 'HIGH' },
  { date: 'Oct 10, 2026', amount: '$42,000.00', riskLevel: 'HIGH' },
  { date: 'Oct 17, 2026', amount: '$38,000.00', riskLevel: 'HIGH' },
  { date: 'Oct 15, 2026', amount: '$15,500.00', riskLevel: 'MEDIUM' },
  { date: 'Oct 07, 2026', amount: '$15,000.00', riskLevel: 'LOW' }
];
