# -*- coding: utf-8 -*-
from flask.ext.wtf import Form
from wtforms import StringField,SubmitField,PasswordField,TextAreaField,SelectField,validators
import sys
reload(sys)
sys.setdefaultencoding('utf8')
class PushForm(Form):
    pushtitle=StringField('条目名',[validators.Required(),validators.Length(min=1,max=60)])
    submit=SubmitField('推送')
class EditProfileForm(Form):
    password=PasswordField('新密码',[validators.Length(min=0,max=30),validators.EqualTo('password2',message='两次输入不一致')])
    password2=PasswordField('确认密码',[validators.Length(min=0,max=30)])
    email=StringField('邮件地址',[validators.Length(min=0,max=30)])
    about_me=TextAreaField('个人签名')
    oripassword=PasswordField('请输入原密码以验证身份',[validators.Required(),validators.Length(min=6,max=30)])
    submit=SubmitField('提交')
class AddUserForm(Form):
    username=StringField('用户名',[validators.Length(min=0,max=30),validators.Required()])
    password=PasswordField('密码',[validators.Length(min=0,max=30),validators.EqualTo('password2',message='两次输入不一致'),validators.Required()])
    password2=PasswordField('确认密码',[validators.Length(min=0,max=30),validators.Required()])
    email=StringField('邮件地址',[validators.Length(min=0,max=30),validators.Required()])
    role=SelectField('职务')
    submit=SubmitField('提交')
    def __init__(self,*args,**kwargs):
        super(AddUserForm,self).__init__(*args,**kwargs)
        self.role.choices=[('guanli','管理员'),('xuncha','巡察姬')]