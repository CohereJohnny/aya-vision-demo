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
    initial_prompt = TextAreaField(
        'Initial Analysis Prompt (Binary Classification)',
        validators=[DataRequired(), Length(min=10, max=1000)],
        render_kw={"rows": 4, "placeholder": "Enter the prompt for initial binary classification (e.g., 'Is a flare burning in this image? Answer with only true or false.')"}
    )
    enhanced_prompt = TextAreaField(
        'Enhanced Analysis Prompt (Detailed Description)',
        validators=[DataRequired(), Length(min=10, max=1000)],
        render_kw={"rows": 4, "placeholder": "Enter the prompt for enhanced analysis of positively identified images (e.g., 'Describe in detail what you see in this image, focusing on the flare.')"}
    )
    submit = SubmitField('Save Settings')
    reset = SubmitField('Reset to Default')

class EnhancedAnalysisForm(FlaskForm):
    """Form for triggering enhanced analysis."""
    custom_prompt = TextAreaField(
        'Custom Prompt for Enhanced Analysis',
        validators=[DataRequired(), Length(min=10, max=1000)],
        render_kw={"rows": 3, "placeholder": "Enter a custom prompt for enhanced analysis or use the default from settings..."}
    )
    submit = SubmitField('Start Enhanced Analysis')
