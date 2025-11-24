"""
LLM integration for generating intelligent summaries of tennis booking results.
Supports both OpenAI and Anthropic APIs.
"""
import os
import json
from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMSummarizer:
    def __init__(self, provider='openai', api_key=None, model=None):
        """
        Initialize LLM client.
        
        Args:
            provider: 'openai' or 'anthropic'
            api_key: API key (defaults to environment variable)
            model: Model to use (defaults based on provider)
        """
        self.provider = provider
        
        if provider == 'openai':
            import openai
            self.client = openai.OpenAI(
                api_key=api_key or os.environ.get('OPENAI_API_KEY')
            )
            self.model = model or 'gpt-4-turbo-preview'
        elif provider == 'anthropic':
            import anthropic
            self.client = anthropic.Anthropic(
                api_key=api_key or os.environ.get('ANTHROPIC_API_KEY')
            )
            self.model = model or 'claude-3-sonnet-20240229'
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def generate_summary(self, log_data: Dict, email_data: List[Dict]) -> str:
        """
        Generate a comprehensive summary combining log and email data.
        
        Args:
            log_data: Summary data from log parser
            email_data: List of parsed email data
            
        Returns:
            Human-readable summary text
        """
        # Prepare the data for the prompt
        context = self._prepare_context(log_data, email_data)
        
        # Create the prompt
        prompt = self._create_prompt(context)
        
        # Generate summary using LLM
        try:
            if self.provider == 'openai':
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that creates clear, concise summaries of tennis court booking results."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                return response.choices[0].message.content
                
            elif self.provider == 'anthropic':
                response = self.client.messages.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                return response.content[0].text
                
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return self._fallback_summary(context)
    
    def _prepare_context(self, log_data: Dict, email_data: List[Dict]) -> Dict:
        """Prepare and reconcile data from logs and emails."""
        context = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'log_summary': log_data,
            'email_confirmations': [],
            'discrepancies': [],
            'insights': []
        }
        
        # Process email confirmations
        for email in email_data:
            if email.get('status') == 'confirmed':
                context['email_confirmations'].append({
                    'court': email.get('court'),
                    'date': email.get('date_str'),
                    'time': email.get('time_str'),
                    'account': email.get('account_email')
                })
        
        # Find discrepancies between logs and emails
        log_successes = [
            attempt for attempt in log_data.get('attempts', [])
            if attempt.get('status') == 'success'
        ]
        
        # Check for successes in logs but not in emails
        for log_success in log_successes:
            found_in_email = False
            for email_conf in context['email_confirmations']:
                if (email_conf['court'] == log_success.get('court') and
                    email_conf['time'] == log_success.get('time')):
                    found_in_email = True
                    break
            
            if not found_in_email:
                context['discrepancies'].append({
                    'type': 'log_only',
                    'court': log_success.get('court'),
                    'time': log_success.get('time'),
                    'message': 'Logged as success but no email confirmation'
                })
        
        # Check for email confirmations not in logs
        for email_conf in context['email_confirmations']:
            found_in_log = False
            for attempt in log_data.get('attempts', []):
                if (attempt.get('court') == email_conf['court'] and
                    attempt.get('time') == email_conf['time']):
                    found_in_log = True
                    break
            
            if not found_in_log:
                context['discrepancies'].append({
                    'type': 'email_only',
                    'court': email_conf['court'],
                    'time': email_conf['time'],
                    'message': 'Email confirmation but not found in logs'
                })
        
        # Generate insights
        if log_data.get('by_court'):
            # Find most successful courts
            court_success_rates = []
            for court, stats in log_data['by_court'].items():
                if stats['attempts'] > 0:
                    success_rate = stats['successes'] / stats['attempts']
                    court_success_rates.append((court, success_rate, stats['attempts']))
            
            court_success_rates.sort(key=lambda x: x[1], reverse=True)
            
            if court_success_rates:
                best_court = court_success_rates[0]
                context['insights'].append(
                    f"Court {best_court[0]} had the highest success rate: "
                    f"{best_court[1]:.1%} ({best_court[2]} attempts)"
                )
            
            # Find courts with no successes
            failed_courts = [
                court for court, stats in log_data['by_court'].items()
                if stats['attempts'] > 0 and stats['successes'] == 0
            ]
            if failed_courts:
                context['insights'].append(
                    f"Courts {', '.join(map(str, failed_courts))} had no successful bookings"
                )
        
        return context
    
    def _create_prompt(self, context: Dict) -> str:
        """Create the prompt for the LLM."""
        prompt = f"""Please generate a comprehensive daily summary of tennis court booking results for {context['date']}.

Data from logs:
- Total attempts: {context['log_summary']['total_attempts']}
- Successful: {context['log_summary']['successful']}
- Failed: {context['log_summary']['failed']}
- Unknown status: {context['log_summary']['unknown']}

By Court Performance:
{json.dumps(context['log_summary']['by_court'], indent=2)}

Email Confirmations Received:
{json.dumps(context['email_confirmations'], indent=2)}

Discrepancies Found:
{json.dumps(context['discrepancies'], indent=2)}

Please create a summary that includes:
1. Overall success rate and key statistics
2. Performance by court (which courts were most/least successful)
3. Any discrepancies between logs and email confirmations
4. Top performing accounts
5. Recommendations for improving booking success
6. Any concerning patterns or issues

Format the summary in a clear, easy-to-read manner with sections and bullet points where appropriate."""
        
        return prompt
    
    def _fallback_summary(self, context: Dict) -> str:
        """Generate a basic summary without LLM."""
        log_summary = context['log_summary']
        
        summary = f"""Tennis Court Booking Summary for {context['date']}
{'='*50}

Overall Statistics:
- Total Attempts: {log_summary['total_attempts']}
- Successful: {log_summary['successful']}
- Failed: {log_summary['failed']}
- Success Rate: {log_summary['successful'] / max(1, log_summary['total_attempts']):.1%}

Court Performance:
"""
        
        for court, stats in sorted(log_summary['by_court'].items()):
            success_rate = stats['successes'] / max(1, stats['attempts'])
            summary += f"- Court {court}: {stats['attempts']} attempts, {stats['successes']} successes ({success_rate:.1%})\n"
        
        summary += f"\nEmail Confirmations: {len(context['email_confirmations'])} received\n"
        
        if context['discrepancies']:
            summary += f"\nDiscrepancies: {len(context['discrepancies'])} found\n"
            for disc in context['discrepancies']:
                summary += f"- {disc['message']} (Court {disc['court']} at {disc['time']})\n"
        
        return summary


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Mock data for testing
    mock_log_data = {
        'total_attempts': 24,
        'successful': 6,
        'failed': 18,
        'unknown': 0,
        'by_court': {
            5: {'attempts': 6, 'successes': 3},
            6: {'attempts': 6, 'successes': 2},
            3: {'attempts': 6, 'successes': 1},
            2: {'attempts': 6, 'successes': 0}
        },
        'attempts': []
    }
    
    mock_email_data = [
        {
            'status': 'confirmed',
            'court': 5,
            'date_str': '2025-09-05',
            'time_str': '18:00',
            'account_email': 'nyuclubtennis+alex@gmail.com'
        }
    ]
    
    # Test with fallback (no API key)
    summarizer = LLMSummarizer(provider='openai')
    summary = summarizer._fallback_summary({
        'date': '2025-09-05',
        'log_summary': mock_log_data,
        'email_confirmations': mock_email_data,
        'discrepancies': [],
        'insights': []
    })
    
    print(summary)





