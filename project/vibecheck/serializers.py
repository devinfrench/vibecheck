from rest_framework import serializers
from .models import Profile, Post, Friendship
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db.models import Q


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'], validated_data['email'], validated_data['password'], 
        first_name=validated_data['first_name'], last_name=validated_data['last_name'])
        profile = Profile.objects.create(user=user, display_name=(user.first_name+ " " + user.last_name))
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid Credentials")


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('__all__')


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('__all__')

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['posts'] = PostSerializer(instance.posts, many=True).data
        return response


class UserSerializer(serializers.ModelSerializer):
    friends = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile', 'friends')

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['profile'] = ProfileSerializer(instance.profile, many=True).data[0]
        return response

    def get_friends(self, instance):
        friendships = Friendship.objects.filter(Q(creator=instance.id) | Q(friend=instance.id))
        return FriendshipSerializer(friendships, many=True, context={'user': instance.username}).data


class FriendshipSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ('__all__')

    def get_profile(self, instance):
        user = instance.creator if self.context.get('user') == instance.friend.username else instance.friend
        print(instance.creator, instance.friend, self.context.get('user'), user)
        return ProfileSerializer(Profile.objects.filter(user=user), many=True).data[0]