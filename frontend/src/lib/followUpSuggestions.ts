/**
 * Static follow-up questions for the handbook topics already in the product.
 * These are questions, not policy facts, and they do not call another model.
 */

const FOLLOW_UPS: Array<{ match: RegExp; prompts: string[] }> = [
  {
    match: /casual/i,
    prompts: [
      "What is the maximum casual leave that can be taken in one month?",
      "Does unused casual leave carry forward?",
    ],
  },
  {
    match: /sick|medical certificate/i,
    prompts: [
      "Is a medical certificate required for sick leave?",
      "Does unused sick leave carry forward?",
    ],
  },
  {
    match: /maternity/i,
    prompts: [
      "How many weeks of maternity leave are provided?",
      "Is paternity leave paid or unpaid?",
    ],
  },
  {
    match: /paternity/i,
    prompts: [
      "Is paternity leave paid or unpaid?",
      "How many weeks of maternity leave are provided?",
    ],
  },
  {
    match: /earned|carry forward|privilege/i,
    prompts: [
      "Can unused earned leave be carried forward, and what is the maximum?",
    ],
  },
  {
    match: /work from home|wfh/i,
    prompts: ["What is the work from home policy?"],
  },
  {
    match: /adoption/i,
    prompts: ["How many days of casual leave is an employee entitled to in a year?"],
  },
];

export function followUpSuggestions(question: string): string[] {
  const match = FOLLOW_UPS.find((item) => item.match.test(question));
  return match?.prompts.slice(0, 2) ?? [
    "How many days of sick leave can an employee take?",
    "What is the work from home policy?",
  ];
}
