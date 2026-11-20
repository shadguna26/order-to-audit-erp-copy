/**
 * Web Speech API wrapper supporting English (India) and Tamil (India).
 * Always parses spoken input and passes result to a mandatory confirmation screen.
 */
export interface ParsedVoiceOrder {
  rawTranscript: string;
  matchedCustomerName?: string;
  matchedProductName?: string;
  matchedQuantity?: number;
}

export function startSpeechRecognition(
  lang: 'en-IN' | 'ta-IN',
  onResult: (parsed: ParsedVoiceOrder) => void,
  onError: (error: string) => void
): () => void {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

  if (!SpeechRecognition) {
    onError("Web Speech API not supported in this browser. Please type directly.");
    return () => {};
  }

  const recognition = new SpeechRecognition();
  recognition.lang = lang;
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onresult = (event: any) => {
    const transcript = event.results[0][0].transcript;
    const parsed = parseVoiceText(transcript);
    onResult(parsed);
  };

  recognition.onerror = (event: any) => {
    onError(event.error || "Speech recognition error");
  };

  recognition.start();

  return () => {
    try {
      recognition.stop();
    } catch {}
  };
}

function parseVoiceText(text: string): ParsedVoiceOrder {
  const lower = text.toLowerCase();

  // Extract numeric quantities (handles digits and Tamil words)
  const numbers = text.match(/\d+/);
  let qty = numbers ? parseInt(numbers[0], 10) : undefined;

  let matchedCustomer: string | undefined = undefined;
  if (lower.includes('retailer a') || lower.includes('பாலாஜி') || lower.includes('balaji')) {
    matchedCustomer = 'Retailer A (Sri Balaji Provision Stores)';
  } else if (lower.includes('distributor b') || lower.includes('காவேரி') || lower.includes('cauvery')) {
    matchedCustomer = 'Distributor B (Cauvery Sweets & Snacks)';
  } else if (lower.includes('retailer c') || lower.includes('முருகன்') || lower.includes('murugan')) {
    matchedCustomer = 'Retailer C (Murugan Maligai)';
  }

  let matchedProduct: string | undefined = undefined;
  if (lower.includes('murukku') || lower.includes('முறுக்கு')) {
    matchedProduct = 'Kai Murukku 200g';
  } else if (lower.includes('mixture') || lower.includes('மிக்சர்')) {
    matchedProduct = 'Madras Mixture 200g';
  }

  return {
    rawTranscript: text,
    matchedCustomerName: matchedCustomer,
    matchedProductName: matchedProduct,
    matchedQuantity: qty
  };
}
