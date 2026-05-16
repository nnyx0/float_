from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models as gis

import cbor2

# Create your models here.

class Role(models.Model):
    id = models.BigAutoField(primary_key=True)
    last_updated_timestamp = models.DateTimeField(auto_now=True, null=True) # Updates timestamp each time the object is save.
    # end of basic fields

    title = models.CharField(max_length=50, null=False,
        help_text='Role assigned for the event')

    def __str__(self):
        return self.title # returns the Role Title

class Patrol(models.Model):
    name = models.CharField(max_length=10)
    description = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return self.name

class Place(models.Model):
    id = models.BigAutoField(primary_key=True)
    last_updated_timestamp = models.DateTimeField(auto_now=True, null=True) # Updates timestamp each time the object is save.
    # end of basic fields
    callsign = models.CharField(max_length=50, null=True, blank=True,
        help_text='Callsign of the Base.')
    place = models.CharField(max_length=50, null=False,
        help_text = 'Location assigned for the event.')
    
    location = gis.PointField(null=True, blank=True, help_text='GPS coordinates of the location.')

    address = models.TextField(max_length=256, null=True, blank=True,
        help_text='Address of the location, if known.')

    def __str__(self):
        return self.place # returns the Place (assigned location)

class UserProfile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    location = models.ForeignKey(Place, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user)

class CheckIn(models.Model):
    class State(models.IntegerChoices):
        CHECKED_IN = 1
        CHECKED_OUT = 2

    patrol = models.ForeignKey(Patrol, on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    location = models.ForeignKey(Place, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(null=False) # Updates timestamp each time the object is save.
    state = models.IntegerField(choices=State)

    def __str__(self):
        return f"{self.patrol} {CheckIn.State(self.state).name} {self.location} @ {self.timestamp}"

class Operator(models.Model):
    id = models.BigAutoField(primary_key=True)
    last_updated_timestamp = models.DateTimeField(auto_now=True, null=True) # Updates timestamp each time the object is save.
    # end of basic fields

    name = models.CharField(max_length=50,
        help_text='Name of the Operator.')
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    callsign = models.CharField(max_length=50, null=True, blank=True,
        help_text='Callsign of the Operator.')
    role = models.ForeignKey('Role', null=True, blank=True, on_delete=models.SET_NULL, related_name='is_operator_role',
        help_text='Select the role of the Operator from the list.')
    base = models.ForeignKey('Place', null=True, blank=True, on_delete=models.SET_NULL, related_name='is_operator_base',
        help_text='Select the place the Operator is assigned to from the list.')
    command_weighting = models.PositiveIntegerField(null=True,
        help_text='Provide the order in which you wish to have this operator appear in the Message dropdown.')

    def __str__(self):
        try:
            callsign = self.base.callsign
        except TypeError:
            callsign = ""
        return f'{self.base} {callsign} ({self.name})' # returns the Operator's name, role, and assigned location
        # this helps reconcile the reported location of the Operator with their assigned location and the reported
        # location to assess if further support is required in the field.

    class Meta:
        ordering = ('command_weighting', 'base', 'name')

class Message(models.Model):
    id = models.BigAutoField(primary_key=True)
    last_updated_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    last_updated_timestamp = models.DateTimeField(auto_now=True, null=True) # Updates timestamp each time the object is save.
    # end of basic fields

    message_entry_timestamp = models.DateTimeField(auto_now_add=False, default=timezone.now, null=True) # Records a timestamp for when the message was initially added.
    sender = models.ForeignKey('Operator', null=True, blank=True, on_delete=models.SET_NULL, related_name='is_sender',
        help_text='Message was sent by this Operator.')
    recipient = models.ForeignKey('Operator', null=True, blank=True, on_delete=models.SET_NULL, related_name='is_recipient',
        help_text='Message was received by this Operator.')
    reported_location = models.CharField(max_length=256, null=True, blank=True,
        help_text='Sender Operator\'s reported location, if provided - recipient location should be recorded if needed as message info.')
    message_info = models.TextField(null=True, blank=True,
        help_text='Message details.')
    incident_ref = models.ForeignKey('Incident', null=True, blank=True, on_delete=models.SET_NULL, related_name="is_incidentmessage_ref",
        help_text='Create a new incident or select an existing incident.')

    def __str__(self):
        sender_name = self.sender.name if self.sender else "Unknown"
        recipient_name = self.recipient.name if self.recipient else "Unknown"
        return f'Message #{self.id}: {self.sender} {sender_name} -> {self.recipient} {recipient_name} RE: {self.incident_ref}' # returns the {Message ID}: {Message Sender} -> {Message Recipient}, and Incident summary

    def serialize(self):
        message = {
            "message_entry_timestamp": self.message_entry_timestamp,
            "sender": self.sender.callsign,
            "recipient": self.recipient.callsign,
            "reported_location": self.reported_location,
            "message_info": self.message_info,
        }
        return cbor2.dumps(message, datetime_as_timestamp=True, string_referencing=True)

    @classmethod
    def deserialize(cls, data):
        message =  cbor2.loads(data)
        new_message = Message(
            message_entry_timestamp = message["message_entry_timestamp"],
            sender = Operator.objects.get_or_create(callsign=message["sender"]),
            recipient = Operator.objects.get_or_create(callsign=message["recipient"]),
            reported_location = message["reported_location"],
            message_info = message["message_info"],
        )
        new_message.save()
        return new_message

class IncidentPatient(models.Model):
    id = models.BigAutoField(primary_key=True)
    last_updated_timestamp = models.DateTimeField(auto_now=True, null=True) # Updates timestamp each time the object is save.
    # end of basic fields

    name = models.CharField(max_length=256, null=True, blank=True, default='UNKNOWN',
        help_text='Name of the patient. Change this field once the name is known.')
    age = models.IntegerField(null=True, blank=True,
        help_text='Approximate age of patient, if known.')
    gender = models.CharField(max_length=50, null=True, blank=True,
        help_text='Reported gender of the patient, if known.')
    contact_phone = models.CharField(max_length = 20, null=True, blank=True,
        help_text='Phone is preferred - obtain if required for follow up after incident has been controlled.')
    contact_email = models.CharField(max_length = 256, null=True, blank=True,
        help_text='Obtain if required for follow up after incident has been controlled.')
    incident_ref = models.ForeignKey('Incident', null=True, blank=True, on_delete=models.SET_NULL, related_name="is_incident_ref",
        help_text='Create a new patient or select an existing patient to allocate a Patient ID (even if details of patient are not known at the time of the message)')

    def __str__(self):
        return f'Patient #{self.id}: {self.name[0]} ({self.gender}, {self.age})' # returns Patient ID: Patient's first initial - this preserves privacy on the dashboard.

class Incident(models.Model):
    id = models.BigAutoField(primary_key=True)
    last_updated_timestamp = models.DateTimeField(auto_now=True) # Updates timestamp each time the object is save.
    # end of basic fields

    # Begin Incident Report
    event_occurance_timestamp = models.DateTimeField(auto_now_add=True, null=True,
        help_text='Time of the incident events occuring') # Creates editable timestamp recording the event time.
    reported_location = models.CharField(max_length=256, null=False, blank=True,
        help_text='What is the reported location of the incident?')
    patient_ref = models.ForeignKey('IncidentPatient', null=True, blank=True, on_delete=models.SET_NULL, related_name="is_incidentpatient_ref",
        help_text='Create a new patient or select an existing patient to allocate a Patient ID (even if details of patient are not known at the time of the message)')
    cause_of_injury = models.TextField(null=True, blank=True,
        help_text='What was the cause of the injury?')
    nature_of_injury = models.TextField(null=True, blank=True,
        help_text='What is the nature of the injury?')
    effects_of_injury = models.TextField(null=True, blank=True,
        help_text='What are the signs/symptoms of the injury, other observations?')
    treatment_provided = models.TextField(null=True, blank=True,
        help_text='What treatment has been provided to the injury at this')
    # End of Incident Report fields

    # Incident Administration fields
    INCIDENT_MESSAGE_TYPE_CHOICES = [
        ('C', 'Child Safety - missing, endangered, threatened, etc'),
        ('E', 'Environmental - location or structure based issues.'),
        ('M', 'Medical - injuries and illness of people involved in the event.'),
        ('O', 'Operational - preventing the effective execution of the event.'),
        ('S', 'Security - threats to people involved in the event.'),
        ('U', 'Undefined threats to the event.'),
    ]
    incident_message_type = models.CharField(
        blank=False, null=True, max_length=1, choices=INCIDENT_MESSAGE_TYPE_CHOICES, default='M',
        help_text='Select the nature of the incident.')

    has_this_been_escalated = models.BooleanField(default=False,
        help_text='Select if this incident has been delegated to another authority, as specificed below:')
    escalated_to = models.CharField(null=True, blank=True, max_length=160,
        help_text='Specify a 000 department, company, custodian, etc.')
    action_taken = models.TextField(null=True, blank=True,
        help_text='Briefly explain what has been done to address the incident situation. Provide as much detail as necessary.')
    is_incident_controlled = models.BooleanField(default=False,
        help_text='Select if this incident has been controlled but has yet to be resolved.')
    is_incident_resolved = models.BooleanField(default=False,
        help_text='Select if this incident has been resolved and no further action is required.')
    # End of Incident Administration fields

    def __str__(self):
        return f'Incident #{self.id}: @ {self.reported_location} [{self.patient_ref} | {self.nature_of_injury}]'

#class IncidentMessage(models.Model):
#    id = models.BigAutoField(primary_key=True)
#    last_updated_timestamp = models.DateTimeField(auto_now=True, null=True) # Updates timestamp each time the object is save.
#    # end of basic fields

#    message_entry_timestamp = models.DateTimeField(auto_now_add=False, null=True) # Creates fixed timestamp recording the message entry time.
#    incident_ref = models.ForeignKey('Incident', null=True, blank=True, on_delete=models.SET_NULL, related_name="is_incidentmessage_ref",
#        help_text='Create a new patient or select an existing patient to allocate a Patient ID (even if details of patient are not known at the time of the message)')
#    sender = models.ForeignKey('Operator', null=True, blank=True, on_delete=models.SET_NULL, related_name='is_incidentmessage_sender',
#        help_text='Message was sent by this Operator.')
#    recipient = models.ForeignKey('Operator', null=True, blank=True, on_delete=models.SET_NULL, related_name='is_incident_recipient',
#        help_text='Message was received by this Operator.')
#    reported_location = models.CharField(max_length=256, null=True, blank=True,
#        help_text='Sender Operator\'s reported location, if provided - recipient location should be recorded if needed as message info.')
#    message_info = models.TextField(null=True, blank=True,
#        help_text='Message details.')
#    # end of message transmission detail fields

#    def __str__(self):
#        return f'Message #{self.id}: {self.sender} -> {self.recipient} RE: {self.incident_ref}' # returns the {Message ID}: {Message Sender} -> {Message Recipient}, and Incident summary
