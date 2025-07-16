"""Twilio + Daily voice bot implementation."""

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv
from loguru import logger
from twilio.rest import Client

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.services.daily import DailyParams, DailyTransport

from pipecat_flows import FlowArgs, FlowManager, FlowResult, NodeConfig

from utils.address_validator import AddressValidator
from utils.email_sender import EmailSender
from utils.date_converter import DateConverter

# Setup logging
load_dotenv()
logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

# Initialize Twilio client
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"), 
    os.getenv("TWILIO_AUTH_TOKEN")
)

# Initialize address validator, email sender, and date converter
address_validator = AddressValidator()
email_sender = EmailSender()
date_converter = DateConverter()

class NameCollectionResult(FlowResult):
    name: str

class DateOfBirthCollectionResult(FlowResult):
    date_of_birth: str

class InsuranceCollectionResult(FlowResult):
    payID: str
    payer_name: str

class AddressCollectionResult(FlowResult):
    address: str

class ReferralCollectionResult(FlowResult):
    # has_referral: str
    referral_doctor: str

class ChiefComplaintCollectionResult(FlowResult):
    chief_complaint: str

class ContactInfoCollectionResult(FlowResult):
    phone_number: str
    email: str = ""

class AppointmentSchedulingResult(FlowResult):
    selected_appointment: str
    custom_time: str = ""
    
# Function handlers
async def collect_name(
    args: FlowArgs, flow_manager: FlowManager
) -> tuple[NameCollectionResult, NodeConfig]:
    """Process name collection."""
    name = args["name"]
    logger.debug(f"collect_name handler executing with name: {name}")

    flow_manager.state["name"] = name
    result = NameCollectionResult(name=name)

    next_node = create_date_of_birth_node()

    return result, next_node

async def collect_date_of_birth(
    args: FlowArgs, flow_manager: FlowManager
) -> tuple[NameCollectionResult, NodeConfig]:
    """Process date of birth collection."""
    date_of_birth = args["date_of_birth"]
    logger.debug(
        f"collect_date_of_birth handler executing with date of birth: {date_of_birth}"
    )

    flow_manager.state["date_of_birth"] = date_of_birth
    result = DateOfBirthCollectionResult(date_of_birth=date_of_birth)

    next_node = create_insurance_node()

    return result, next_node


async def collect_insurance(
    args: FlowArgs, flow_manager: FlowManager
) -> tuple[InsuranceCollectionResult, NodeConfig]:
    """Process insurance information."""
    payer_name = args["payer_name"]
    payerID = args["payID"]
    logger.debug(
        f"collect_insurance handler executing with insurance: {payer_name}, {payerID}"
    )

    flow_manager.state["payer_name"] = payer_name
    flow_manager.state["payID"] = payerID
    result = InsuranceCollectionResult(payer_name=payer_name, payID=payerID)

    next_node = create_referral_node()

    return result, next_node

async def collect_referral(
    args: FlowArgs, flow_manager: FlowManager
) -> tuple[ReferralCollectionResult, NodeConfig]:
    """Process referral information."""
    referral_name = args["referral"]
    logger.debug(f"collect_referral handler executing with referral: {referral_name}")

    flow_manager.state["referral_doctor"] = referral_name
    result = ReferralCollectionResult(referral=referral_name)

    next_node = create_chief_complaint_node()

    return result, next_node

async def collect_chief_complaint(
    args: FlowArgs, flow_manager: FlowManager
) -> tuple[ChiefComplaintCollectionResult, NodeConfig]:
    """Process chief complaint information."""
    chief_complaint = args["chief_complaint"]
    logger.debug(
        f"collect_chief_complaint handler executing with chief complaint: {chief_complaint}"
    )

    flow_manager.state["chief_complaint"] = chief_complaint
    result = ChiefComplaintCollectionResult(chief_complaint=chief_complaint)

    next_node = create_address_node()

    return result, next_node

async def collect_address(
    args: FlowArgs, flow_manager: FlowManager
) -> tuple[AddressCollectionResult, NodeConfig]:
    """Process address information with validation."""
    address = args["address"]
    logger.debug(f"collect_address handler executing with address: {address}")

    # Validate the address using Google Maps API
    try:
        is_valid, address_data, error_message = address_validator.validate_address(address)
        print(is_valid)
        if is_valid:
            # Address is valid, store the formatted address
            formatted_address = address_data.get('formatted_address', address)
            flow_manager.state["address"] = formatted_address
            flow_manager.state["address_data"] = address_data
            
            logger.info(f"Address validated successfully: {formatted_address}")
            result = AddressCollectionResult(address=formatted_address)
            next_node = create_contact_info_node()
            
        else:
            # Address validation failed, ask for clarification
            logger.warning(f"Address validation failed: {error_message}")
            flow_manager.state["address_validation_error"] = error_message
            
            # Stay on the same node to ask for address again
            result = AddressCollectionResult(address="")
            next_node = create_address_retry_node(error_message)
            
    except Exception as e:
        # Handle validation service errors gracefully
        logger.error(f"Address validation service error: {e}")
        # Accept the address as-is if validation service fails
        flow_manager.state["address"] = address
        result = AddressCollectionResult(address=address)
        next_node = create_contact_info_node()

    return result, next_node

async def collect_contact_info(
    args: FlowArgs, flow_manager: FlowManager
) -> tuple[ContactInfoCollectionResult, NodeConfig]:
    """Process contact information."""
    phone_number = args["phone_number"]
    email = args.get("email", "")
    logger.debug(
        f"collect_contact_info handler executing with phone: {phone_number}, email: {email}"
    )

    flow_manager.state["phone_number"] = phone_number
    flow_manager.state["email"] = email
    result = ContactInfoCollectionResult(phone_number=phone_number, email=email)

    next_node = create_appointment_scheduling_node()

    return result, next_node

async def schedule_appointment(
    args: FlowArgs, flow_manager: FlowManager
) -> tuple[AppointmentSchedulingResult, NodeConfig]:
    """Process appointment scheduling with date conversion."""
    appointment_choice = args.get("appointment_choice", "").lower()
    custom_time = args.get("custom_time", "")
    
    logger.debug(f"schedule_appointment handler executing with choice: {appointment_choice}, custom_time: {custom_time}")
    
    # Handle different appointment selection scenarios
    selected_appointment = ""
    
    if "nothing works" in appointment_choice or "none work" in appointment_choice or "not available" in appointment_choice:
        # Patient said nothing works, use their custom time
        selected_appointment = custom_time if custom_time else "Custom time requested"
        flow_manager.state["custom_time"] = custom_time
    elif "anything works" in appointment_choice or "any time" in appointment_choice or "all work" in appointment_choice:
        # Patient said anything works, default to tomorrow at 3pm
        selected_appointment = "tomorrow at 3pm"
    elif "tomorrow" in appointment_choice and "monday" in appointment_choice:
        # Patient gave two options, pick the first one (tomorrow)
        selected_appointment = "tomorrow at 3pm"
    elif "monday" in appointment_choice and "wednesday" in appointment_choice:
        # Patient gave two options, pick the first one (Monday)
        selected_appointment = "next Monday at 10am"
    elif "tomorrow" in appointment_choice:
        selected_appointment = "tomorrow at 3pm"
    elif "monday" in appointment_choice:
        selected_appointment = "next Monday at 10am"
    elif "wednesday" in appointment_choice:
        selected_appointment = "next Wednesday at 11am"
    else:
        # Default to tomorrow if unclear
        selected_appointment = "tomorrow at 3pm"
    
    # Convert the relative date to actual calendar date using the date converter
    try:
        converted_appointment = date_converter.convert_relative_date(selected_appointment)
        logger.info(f"Converted appointment: '{selected_appointment}' → '{converted_appointment}'")
        
        # Store both the original relative date and the converted date
        flow_manager.state["selected_appointment"] = selected_appointment
        flow_manager.state["converted_appointment"] = converted_appointment
        flow_manager.state["custom_time"] = custom_time
        
        # Use the converted date for email confirmation
        appointment_for_email = converted_appointment
        
    except Exception as e:
        logger.error(f"Error converting appointment date: {e}")
        # Fallback to original appointment if conversion fails
        flow_manager.state["selected_appointment"] = selected_appointment
        flow_manager.state["converted_appointment"] = selected_appointment
        flow_manager.state["custom_time"] = custom_time
        appointment_for_email = selected_appointment
    
    # Send appointment confirmation email
    try:
        patient_data = {
            'name': flow_manager.state.get('name', 'Unknown'),
            'date_of_birth': flow_manager.state.get('date_of_birth', 'Not provided'),
            'address': flow_manager.state.get('address', 'Not provided'),
            'phone_number': flow_manager.state.get('phone_number', 'Not provided'),
            'payer_name': flow_manager.state.get('payer_name', 'Not provided'),
            'chief_complaint': flow_manager.state.get('chief_complaint', 'Not provided')
        }
        
        email_sent = email_sender.send_appointment_confirmation(patient_data, appointment_for_email)
        if email_sent:
            logger.info("Appointment confirmation email sent successfully")
        else:
            logger.warning("Failed to send appointment confirmation email")
            
    except Exception as e:
        logger.error(f"Error sending appointment confirmation email: {e}")
    
    result = AppointmentSchedulingResult(selected_appointment=selected_appointment, custom_time=custom_time)
    
    next_node = create_end_node()
    
    return result, next_node

async def end_quote(args: FlowArgs) -> tuple[FlowResult, NodeConfig]:
    """Handle quote completion."""
    logger.debug("end_quote handler executing")
    result = {"status": "completed"}
    next_node = create_end_node()
    return result, next_node


# Node configurations
def create_initial_node() -> NodeConfig:
    """Create the initial node asking for name."""
    return {
        "name": "initial",
        "role_messages": [
            {
                "role": "system",
                "content": (
                    "You are a friendly medical agent. Your responses will be "
                    "converted to audio, so avoid special characters. Always use "
                    "the available functions to progress the conversation naturally."
                    "Introduce yourself as Dr. Smith's medical AI assistant, that's it. Do not ask for the patient's name yet"
                ),
            }
        ],
        "task_messages": [
            {
                "role": "system",
                "content": "Do not introduce yourself twice. Start by asking how they are doing today, wait for them to respond, then ask for their name",
            }
        ],
        "functions": [
            {
                "type": "function",
                "function": {
                    "name": "collect_name",
                    "handler": collect_name,
                    "description": "Record customer's name",
                    "parameters": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                        "required": ["name"],
                    },
                },
            }
        ],
    }

def create_date_of_birth_node() -> NodeConfig:
    """Create node for collecting date of birth."""
    return {
        "name": "date_of_birth",
        "task_messages": [
            {
                "role": "system",
                "content": "Ask about the customer's date of birth.",
            }
        ],
        "functions": [
            {
                "type": "function",
                "function": {
                    "name": "collect_date_of_birth",
                    "handler": collect_date_of_birth,
                    "description": "Record date of birth",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date_of_birth": {"type": "string", "format": "date"}
                        },
                        "required": ["date_of_birth"],
                    },
                },
            }
        ],
    }

def create_insurance_node() -> NodeConfig:
    """Create node for collecting insurance information."""
    return {
        "name": "insurance",
        "task_messages": [
            {
                "role": "system",
                "content": "Ask about the customer's insurance information.",
            }
        ],
        "functions": [
            {
                "type": "function",
                "function": {
                    "name": "collect_insurance",
                    "handler": collect_insurance,
                    "description": "Record insurance information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "payer_name": {"type": "string"},
                            "payID": {"type": "string"}
                        },
                        "required": ["payer_name", "payID"],
                    },
                },
            }
        ],
    }

def create_referral_node() -> NodeConfig:
    """Create node for collecting referral information."""
    return {
        "name": "referral",
        "task_messages": [
            {
                "role": "system",
                "content": "Ask about the customer's referral information. "
                "wait for the customer to answer whether they have a referral or not; "
                "Record the referral name if they say so; "
                "if they say they do not have a referral, ask about their chief complaint",
            }
        ],
        "functions": [
            {
                "type": "function",
                "function": {
                    "name": "collect_referral",
                    "handler": collect_referral,
                    "description": "Record referral information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "referral_name": {"type": "string"}
                        },
                        "required": ["referral_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "collect_chief_complaint",
                    "handler": collect_chief_complaint,
                    "description": "Record the patient's chief complaint or reason for visit",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "chief_complaint": {"type": "string"}
                        },
                        "required": ["chief_complaint"],
                    },
                },
            }
        ],
    }

def create_chief_complaint_node() -> NodeConfig:
    """Create node for collecting chief complaint information."""
    return {
        "name": "chief_complaint",
        "task_messages": [
            {
                "role": "system",
                "content": "Ask about the reason the customer is calling in today - their chief complaint or main concern.",
            }
        ],
        "functions": [
            {
                "type": "function",
                "function": {
                    "name": "collect_chief_complaint",
                    "handler": collect_chief_complaint,
                    "description": "Record the patient's chief complaint or reason for visit",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "chief_complaint": {"type": "string"}
                        },
                        "required": ["chief_complaint"],
                    },
                },
            }
        ],
    }

def create_address_node() -> NodeConfig:
    """Create node for collecting address information."""
    return {
        "name": "address",
        "task_messages": [
            {
                "role": "system",
                "content": "Ask for the customer's address. "
                "Make sure to validate the address and ask for clarification if it seems incomplete or invalid. "
                "If the user did not provide city, state or zip code, check with them if it is the same as the validated address from Google Maps API",
            }
        ],
        "functions": [
            {
                "type": "function",
                "function": {
                    "name": "collect_address",
                    "handler": collect_address,
                    "description": "Record the patient's address",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "address": {"type": "string"}
                        },
                        "required": ["address"],
                    },
                },
            }
        ],
    }

def create_address_retry_node(error_message: str) -> NodeConfig:
    """Create node for retrying address collection after validation failure."""
    return {
        "name": "address_retry",
        "task_messages": [
            {
                "role": "system",
                "content": f"The address provided could not be validated. {error_message} Please ask the customer to provide their complete address again, including street number, street name, city, state, and zip code.",
            }
        ],
        "functions": [
            {
                "type": "function",
                "function": {
                    "name": "collect_address",
                    "handler": collect_address,
                    "description": "Record the patient's address after retry",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "address": {"type": "string"}
                        },
                        "required": ["address"],
                    },
                },
            }
        ],
    }

def create_contact_info_node() -> NodeConfig:
    """Create node for collecting contact information."""
    return {
        "name": "contact_info",
        "task_messages": [
            {
                "role": "system",
                "content": "Ask for the customer's contact information. Phone number is required, but email is optional. Make sure to get a valid phone number format.",
            }
        ],
        "functions": [
            {
                "type": "function",
                "function": {
                    "name": "collect_contact_info",
                    "handler": collect_contact_info,
                    "description": "Record the patient's contact information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "phone_number": {"type": "string"},
                            "email": {"type": "string"}
                        },
                        "required": ["phone_number"],
                    },
                },
            }
        ],
    }

def create_appointment_scheduling_node() -> NodeConfig:
    """Create node for scheduling appointments."""
    return {
        "name": "appointment_scheduling",
        "task_messages": [
            {
                "role": "system",
                "content": (
                    "Offer the patient available appointment times with Dr. Smith: "
                    "tomorrow at 3pm, next Monday at 10am, or next Wednesday at 11am. "
                    "Ask which time works best for them. If they say nothing works, ask when they are available. "
                    "If they say anything works, offer tomorrow at 3pm. "
                    "If they give multiple options, pick the first one mentioned. "
                    "Convert the selected time to a standardized format for scheduling but do not tell the patient about this process. "
                ),
            }
        ],
        "functions": [
            {
                "type": "function",
                "function": {
                    "name": "schedule_appointment",
                    "handler": schedule_appointment,
                    "description": "Schedule an appointment based on patient preference",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "appointment_choice": {"type": "string"},
                            "custom_time": {"type": "string"}
                        },
                        "required": ["appointment_choice"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "end_quote",
                    "handler": end_quote,
                    "description": "Complete the quote process",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ],
    }

def create_end_node() -> NodeConfig:
    """Create the final node."""
    return {
        "name": "end",
        "task_messages": [
            {
                "role": "system",
                "content": (
                    "Thank the customer for their time and end the conversation. "
                    "Mention that an email has been sent to confirm their appointment. "
                    "If available, mention the specific appointment date and time from the converted_appointment in the flow state."
                ),
            }
        ],
        "post_actions": [{"type": "end_conversation"}],
    }

async def run_bot(room_url: str, token: str, call_id: str, sip_uri: str) -> None:
    """Run the voice bot with the given parameters.

    Args:
        room_url: The Daily room URL
        token: The Daily room token
        call_id: The Twilio call ID
        sip_uri: The Daily SIP URI for forwarding the call
    """
    logger.info(f"Starting bot with room: {room_url}")
    logger.info(f"SIP endpoint: {sip_uri}")

    call_already_forwarded = False

    # Setup the Daily transport
    transport = DailyTransport(
        room_url,
        token,
        "Phone Bot",
        DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            transcription_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        ),
    )

    # Setup TTS service
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="71a7ad14-091c-4e8e-a314-022ece01c121",  # British Reading Lady
    )

    # Setup LLM service
    llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")

    # Setup the conversational context
    context = OpenAILLMContext()
    context_aggregator = llm.create_context_aggregator(context)

    # Build the pipeline
    pipeline = Pipeline(
        [
            transport.input(),
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    # Create the pipeline task
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    # Initialize flow manager with transition callback
    flow_manager = FlowManager(
        task=task,
        llm=llm,
        context_aggregator=context_aggregator,
    )

    # Handle participant joining
    @transport.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport, participant):
        logger.info(f"First participant joined: {participant['id']}")
        await transport.capture_participant_transcription(participant["id"])
        await task.queue_frames([context_aggregator.user().get_context_frame()])
        await flow_manager.initialize(create_initial_node())

    # Handle participant leaving
    @transport.event_handler("on_participant_left")
    async def on_participant_left(transport, participant, reason):
        logger.info(f"Participant left: {participant['id']}, reason: {reason}")
        await task.cancel()

    # Handle call ready to forward
    @transport.event_handler("on_dialin_ready")
    async def on_dialin_ready(transport, cdata):
        nonlocal call_already_forwarded

        # We only want to forward the call once
        # The on_dialin_ready event will be triggered for each sip endpoint provisioned
        if call_already_forwarded:
            logger.warning("Call already forwarded, ignoring this event.")
            return

        logger.info(f"Forwarding call {call_id} to {sip_uri}")

        try:
            # Update the Twilio call with TwiML to forward to the Daily SIP endpoint
            twilio_client.calls(call_id).update(
                twiml=f"<Response><Dial><Sip>{sip_uri}</Sip></Dial></Response>"
            )
            logger.info("Call forwarded successfully")
            call_already_forwarded = True
        except Exception as e:
            logger.error(f"Failed to forward call: {str(e)}")
            raise

    @transport.event_handler("on_dialin_connected")
    async def on_dialin_connected(transport, data):
        logger.debug(f"Dial-in connected: {data}")

    @transport.event_handler("on_dialin_stopped")
    async def on_dialin_stopped(transport, data):
        logger.debug(f"Dial-in stopped: {data}")

    @transport.event_handler("on_dialin_error")
    async def on_dialin_error(transport, data):
        logger.error(f"Dial-in error: {data}")
        # If there is an error, the bot should leave the call
        # This may be also handled in on_participant_left with
        # await task.cancel()

    @transport.event_handler("on_dialin_warning")
    async def on_dialin_warning(transport, data):
        logger.warning(f"Dial-in warning: {data}")

    # Run the pipeline
    runner = PipelineRunner()
    await runner.run(task)

    @transport.event_handler("on_transcription_message")
    async def on_transcription_message(transport, message):
        """Handle transcription messages from Daily."""
        print(f"Transcription message: {message['text']}")
        # You can process the transcription here if needed
        # For example, you could send it to the LLM for further processing

async def main():
    """Parse command line arguments and run the bot."""
    parser = argparse.ArgumentParser(description="Daily + Twilio Voice Bot")
    parser.add_argument("-u", type=str, required=True, help="Daily room URL")
    parser.add_argument("-t", type=str, required=True, help="Daily room token")
    parser.add_argument("-i", type=str, required=True, help="Twilio call ID")
    parser.add_argument("-s", type=str, required=True, help="Daily SIP URI")

    args = parser.parse_args()

    # Validate required arguments
    if not all([args.u, args.t, args.i, args.s]):
        logger.error("All arguments (-u, -t, -i, -s) are required")
        parser.print_help()
        sys.exit(1)

    await run_bot(args.u, args.t, args.i, args.s)


if __name__ == "__main__":
    asyncio.run(main())
