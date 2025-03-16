from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import SubmitField, TextAreaField, StringField
from wtforms.validators import DataRequired, Length

class ImageUploadForm(FlaskForm):
    """Form for uploading multiple images."""
    images = FileField('Select Images', validators=[DataRequired()], render_kw={"multiple": True})
    submit = SubmitField('Upload and Analyze')

class SettingsForm(FlaskForm):
    """Form for configuring application settings."""
    subject = StringField(
        'Detection Subject',
        validators=[DataRequired(), Length(min=2, max=50)],
        render_kw={"placeholder": "Enter what you're detecting (e.g., Flare, Building, Vehicle)"}
    )
    prompt = TextAreaField(
        'Master Prompt for Image Analysis',
        validators=[DataRequired(), Length(min=10, max=1000)],
        render_kw={"rows": 5, "placeholder": "Enter the prompt to send to the model for image analysis..."}
    )
    submit = SubmitField('Save Settings')
    reset = SubmitField('Reset to Default')
