export function address(value){if(!/^0x[0-9a-fA-F]{40}$/.test(value))throw Error('Enter a valid 20-byte address.');return value;}
export function integer(value){const n=Number(value);if(!Number.isSafeInteger(n)||n<0)throw Error('Enter a non-negative safe integer.');return n;}
export function digest(value){if(!/^[0-9a-f]{64}$/.test(value))throw Error('Enter a lowercase 64-character SHA-256 digest.');return value;}
export function commit(value){if(!/^[0-9a-f]{40}$/.test(value))throw Error('Enter a full lowercase 40-character Git commit.');return value;}
export function timestamp(value){const n=Date.parse(value);if(!Number.isFinite(n))throw Error('Complete the expiry date and time.');return Math.floor(n/1000);}
export function succeeded(receipt){const leaders=receipt?.consensus_data?.leader_receipt||[];return receipt?.result_name==='MAJORITY_AGREE'&&leaders.some(x=>x.execution_result==='SUCCESS'&&x.result?.status==='return');}
